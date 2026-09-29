import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [question, setQuestion] = useState("");
  const [askedQuestion, setAskedQuestion] = useState("");
  const [parts, setParts] = useState([]);
  const [selectedPart, setSelectedPart] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [engineeringReview, setEngineeringReview] = useState("");
  const [ambiguousParts, setAmbiguousParts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);
  const [error, setError] = useState("");
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setDataLoaded(true);
      setError("");

      const response = await fetch(`${API}/cad/analyze-file`);

      if (!response.ok) {
        throw new Error("Failed to load CAD parts");
      }

      const data = await response.json();
      const loadedParts = data.parts || [];
      setParts(loadedParts);

      if (loadedParts.length > 0) {
        await loadResolvedPart(loadedParts[0].part_id);
      }
    } catch (err) {
      setError(err.message || "Failed to load CAD data");
    } finally {
      setDataLoading(false);
    }
  }

  async function askEngineeringAI(customQuestion = null) {
    const userQuestion = (customQuestion ?? question).trim();

    if (!userQuestion) return;

    try {
      setLoading(true);
      setError("");
      setAmbiguousParts([]);
      setAskedQuestion(userQuestion);
      setEngineeringReview("");

      const response = await fetch(`${API}/cad/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userQuestion })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Engineering AI request failed");
      }

      if (data.status === "ambiguous") {
        setAmbiguousParts(data.parts || []);
        return;
      }

      if (data.status === "not_found") {
        setError(data.message || "I could not identify a CAD part from your question.");
        return;
      }

      await loadResolvedPart(data.part.part_id, data.engineering_review || "");
    } catch (err) {
      setError(err.message || "Engineering AI request failed");
    } finally {
      setLoading(false);
    }
  }

  async function loadResolvedPart(partId, review = "") {
    const [partResponse, intelligenceResponse] = await Promise.all([
      fetch(`${API}/cad/parts/${partId}`),
      fetch(`${API}/cad/parts/${partId}/intelligence`)
    ]);

    if (!partResponse.ok) {
      throw new Error("Failed to load CAD part");
    }

    if (!intelligenceResponse.ok) {
      throw new Error("Failed to load CAD intelligence");
    }

    const part = await partResponse.json();
    const intelligenceData = await intelligenceResponse.json();

    setSelectedPart(part);
    setIntelligence(intelligenceData);
    setEngineeringReview(review);
  }

  async function selectAmbiguousPart(part) {
    const clarifiedQuestion = `${askedQuestion} Part number: ${part.part_number}`;
    await askEngineeringAI(clarifiedQuestion);
  }

  function submitQuestion(event) {
    event.preventDefault();
    askEngineeringAI();
  }

  function useExample(example) {
    setQuestion(example);
    askEngineeringAI(example);
  }

  function decisionClass(decision) {
    if (decision === "reuse_candidate") return "decision reuse";
    if (decision === "engineering_review") return "decision review";
    return "decision reject";
  }

  const whereUsed = intelligence?.where_used || [];
  const similarParts = intelligence?.similar_parts || [];
  const reuseCandidates = intelligence?.reuse_candidates || [];
  const futureCandidates = intelligence?.future_development_candidates || [];
  const findings = selectedPart?.findings || [];


  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>CAD Part Intelligence</h1>
          <p>AI Engineering Design Review &amp; Part Reuse Intelligence</p>
        </div>

        <button
            className="load-data-button"
            onClick={loadData}
            disabled={dataLoaded}
          >
            {dataLoaded ? "✓ Data Loaded" : "Load Data"}
        </button>

          {/* {dataLoaded && (
            <p className="data-loaded-message">
              Data is loaded.
            </p>
          )} */}
      </header>

      <main className="main-content">
        <section className="assistant-card">
          <div className="assistant-heading">
            <div>
              <span className="eyebrow">ENGINEERING ASSISTANCE</span>
              <h2>Ask an engineering question</h2>
              <p>Ask about the loaded CAD data using a part number, part name, or natural language.</p>
            </div>
            {selectedPart && <span className="loaded-part-badge">Loaded: {selectedPart.part_number}</span>}
          </div>

          <form onSubmit={submitQuestion} className="question-form">
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Example: Can I consider BRACKET-001 for a new engine development?"
              rows={3}
            />
            <button className="ask-button" type="submit" disabled={loading || !question.trim()}>
              {loading ? "Analyzing..." : "Ask Engineering AI"}
            </button>
          </form>

          <div className="examples">
            <span>Try:</span>
            <button onClick={() => useExample("Can I consider BRACKET-001 for a new engine development?")}>Can I consider BRACKET-001 for a new engine development?</button>
            <button onClick={() => useExample("Tell me about the Engine Mounting Bracket.")}>Tell me about the Engine Mounting Bracket.</button>
            <button onClick={() => useExample("Show me the bracket.")}>Show me the bracket.</button>
          </div>
        </section>

        {error && !loading && (
          <div className="result-message error-message">
            <strong>Unable to answer the question</strong>
            <span>{error}</span>
          </div>
        )}

        {ambiguousParts.length > 0 && !loading && (
          <section className="result-card ambiguity-card">
            <div className="result-card-header">
              <div>
                <span className="eyebrow">PART IDENTIFICATION</span>
                <h2>Multiple parts match your question</h2>
                <p>Select the part you mean and the analysis will continue.</p>
              </div>
            </div>

            <div className="candidate-grid">
              {ambiguousParts.map((part) => (
                <button key={part.part_id} className="candidate-card" onClick={() => selectAmbiguousPart(part)}>
                  <span className="candidate-number">{part.part_number}</span>
                  <strong>{part.part_name}</strong>
                  <span>{part.part_id}</span>
                  <em>Use this part →</em>
                </button>
              ))}
            </div>
          </section>
        )}

        {selectedPart && intelligence && (
          <div className="data-content">
            {askedQuestion && engineeringReview && !loading && (
              <section className="result-card review-card">
                <div className="result-card-header">
                  <div>
                    <span className="eyebrow">AI ENGINEERING RESPONSE</span>
                    <h2>Answer to your question</h2>
                    <p>{askedQuestion}</p>
                  </div>
                  <span className="ai-badge">AI</span>
                </div>

                <div className="review-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{engineeringReview}</ReactMarkdown>
                </div>
              </section>
            )}

            <section className="result-card part-summary-card">
              <div className="part-summary-main">
                <span className="eyebrow">CAD PART DATA</span>
                <h2>{selectedPart.part_name}</h2>
                <p>{selectedPart.part_number} · {selectedPart.part_id} · Revision {selectedPart.revision}</p>
              </div>
              <span className="status-badge">{selectedPart.lifecycle?.status || "-"}</span>
            </section>

            <div className="section-grid">
              <section className="result-card">
                <SectionTitle title="Part Information" />
                <div className="part-image-container">
                  <img
                    src={`${API}${selectedPart.image_url}`}
                    alt={selectedPart.part_name}
                    className="part-image"
                  />
                </div>
                <div className="info-grid">
                  <Info label="Material" value={selectedPart.material} />
                  <Info label="Manufacturing" value={selectedPart.manufacturing_process} />
                  <Info label="Functional Category" value={selectedPart.functional_category} />
                  <Info label="Application" value={selectedPart.design_context?.application || selectedPart.application} />
                  <Info label="Criticality" value={selectedPart.design_context?.criticality || selectedPart.criticality} />
                  <Info label="Load Type" value={selectedPart.design_context?.load_type || selectedPart.load_type} />
                </div>
              </section>

              <section className="result-card">
                <SectionTitle title="Geometry & Engineering" />
                <div className="info-grid">
                  <Info label="Volume" value={formatValue(selectedPart.geometry?.volume_mm3, "mm³")} />
                  <Info label="Mass" value={formatValue(selectedPart.geometry?.mass_kg, "kg")} />
                  <Info label="Min Wall" value={formatValue(selectedPart.engineering?.min_wall_thickness_mm, "mm")} />
                  <Info label="Tolerance" value={formatValue(selectedPart.engineering?.tolerance_mm, "mm")} />
                  <Info label="Holes" value={selectedPart.features?.hole_count} />
                  <Info label="GD&T" value={selectedPart.pmi?.gd_t_count} />
                </div>
              </section>
            </div>

            <section className="result-card">
              <SectionTitle title="Where Used" count={`${whereUsed.length} products`} />
              {whereUsed.length === 0 ? (
                <EmptySection text="No product usage records found." />
              ) : (
                <div className="data-table">
                  <div className="table-row table-head">
                    <span>Product</span><span>Family</span><span>Role</span><span>Qty</span><span>Status</span>
                  </div>
                  {whereUsed.map((item) => (
                    <div className="table-row" key={`${item.product_id}-${item.usage_role}`}>
                      <span><strong>{item.product_id}</strong><small>{item.product_name}</small></span>
                      <span>{item.product_family}</span><span>{item.usage_role}</span><span>{item.quantity}</span><span>{item.lifecycle_status}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="result-card">
              <SectionTitle title="Similar Parts" count={`${similarParts.length} candidates`} />
              {similarParts.length === 0 ? (
                <EmptySection text="No similar parts found." />
              ) : (
                <div className="similar-grid">
                  {similarParts.slice(0, 6).map((part) => (
                    <div className="similar-card" key={part.part_id}>
                      <div><strong>{part.part_number}</strong><span>{part.part_name}</span></div>
                      <b>{part.similarity_score}%</b>
                      <small>{part.material} · {part.manufacturing_process}</small>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="result-card">
              <SectionTitle title="Reuse Candidates" count={`${reuseCandidates.length} candidates`} />
              {reuseCandidates.length === 0 ? (
                <EmptySection text="No reuse candidates found." />
              ) : (
                <div className="reuse-list">
                  {reuseCandidates.slice(0, 5).map((candidate) => (
                    <div className="reuse-card" key={candidate.candidate_part_id}>
                      <div className="reuse-main"><strong>{candidate.candidate_part_number}</strong><span>{candidate.candidate_part_id}</span></div>
                      <div className="reuse-score">{candidate.similarity_score}%</div>
                      <div className={decisionClass(candidate.decision)}>{candidate.decision?.replaceAll("_", " ")}</div>
                      <div className="reuse-details">
                        <div><b>Reasons</b>{(candidate.reasons || []).slice(0, 3).map((reason, index) => <span key={index}>✓ {reason}</span>)}</div>
                        <div><b>Warnings</b>{(candidate.warnings || []).slice(0, 3).map((warning, index) => <span key={index}>⚠ {warning}</span>)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="result-card">
              <SectionTitle title="Future Development Candidates" count={`${futureCandidates.length} candidates`} />
              {futureCandidates.length === 0 ? (
                <EmptySection text="No future-development candidates returned by the intelligence service." />
              ) : (
                <div className="future-grid">
                  {futureCandidates.map((candidate, index) => (
                    <div className="future-card" key={candidate.part_id || candidate.candidate_part_id || index}>
                      <strong>{candidate.part_number || candidate.candidate_part_number}</strong>
                      <span>{candidate.part_name || candidate.candidate_part_name}</span>
                      {candidate.similarity_score != null && <b>{candidate.similarity_score}% similarity</b>}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="result-card">
              <SectionTitle title="Inspection Findings" count={`${findings.length} findings`} />
              {findings.length === 0 ? (
                <EmptySection text="No inspection findings." />
              ) : (
                <div className="finding-list">
                  {findings.map((finding, index) => (
                    <div className="finding" key={index}>
                      <span className={`severity ${finding.severity}`}>{finding.severity}</span>
                      <div><strong>{finding.type}</strong><p>{finding.message}</p></div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {!selectedPart && dataLoading && (
          <div className="loading-state"><div className="spinner" /><h3>Loading CAD data</h3><p>Loading the available parts and engineering intelligence...</p></div>
        )}
      </main>
    </div>
  );
}

function SectionTitle({ title, count }) {
  return <div className="section-title-row"><h3>{title}</h3>{count && <span>{count}</span>}</div>;
}

function Info({ label, value }) {
  return <div className="info-item"><span>{label}</span><strong>{value ?? "-"}</strong></div>;
}

function EmptySection({ text }) {
  return <div className="empty-section">{text}</div>;
}

function formatValue(value, unit) {
  return value == null ? "-" : `${value} ${unit}`;
}

export default App;
