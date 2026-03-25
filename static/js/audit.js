/*
  audit.js
  Renders audit results, violations, risks and the audit pipeline timeline.
*/

const auditResultsEndpoint = "/api/compliance/results/?format=json";

/* ---------------------------------------------------
   Audit Pipeline Timeline
--------------------------------------------------- */

function renderAuditPipeline(pipeline) {

  const container = document.getElementById("audit-pipeline-timeline");
  if (!container) return;

  container.innerHTML = "";

  if (!Array.isArray(pipeline) || pipeline.length === 0) {
    container.innerHTML =
      '<div class="text-gray-500 text-sm">No pipeline data available.</div>';
    return;
  }

  const statusIcons = {
    completed:
      '<span class="timeline-step__icon inline-flex items-center justify-center w-10 h-10 rounded-full bg-green-100 text-green-600"><i class="fa fa-check"></i></span>',
    processing:
      '<span class="timeline-step__icon inline-flex items-center justify-center w-10 h-10 rounded-full bg-indigo-100 text-indigo-600"><i class="fa fa-spinner fa-spin"></i></span>',
    pending:
      '<span class="timeline-step__icon inline-flex items-center justify-center w-10 h-10 rounded-full bg-slate-100 text-slate-600"><i class="fa fa-circle"></i></span>',
    failed:
      '<span class="timeline-step__icon inline-flex items-center justify-center w-10 h-10 rounded-full bg-red-100 text-red-600"><i class="fa fa-times"></i></span>',
  };

  pipeline.forEach((step) => {

    const stepDiv = document.createElement("div");
    stepDiv.className = "timeline-step";

    const icon = statusIcons[step.status] || statusIcons.pending;

    stepDiv.innerHTML = icon;

    const body = document.createElement("div");
    body.className = "timeline-step__body";

    const stepName = step.step || "Step";
    const status = step.status || "pending";

    const title = document.createElement("div");
    title.className = "timeline-step__title";
    title.innerHTML = `
      <span>${stepName}</span>
      <span class="timeline-step__status">${status}</span>
    `;

    body.appendChild(title);

    const toggle = document.createElement("button");
    toggle.className = "timeline-step__toggle";
    toggle.innerHTML = '<i class="fa fa-chevron-down"></i> Show details';

    const detailsDiv = document.createElement("div");
    detailsDiv.className = "timeline-step__details hidden";
    detailsDiv.innerHTML = renderStepDetails(step.details);

    toggle.addEventListener("click", () => {
      const expanded = !detailsDiv.classList.contains("hidden");
      detailsDiv.classList.toggle("hidden");
      toggle.innerHTML = expanded
        ? '<i class="fa fa-chevron-down"></i> Show details'
        : '<i class="fa fa-chevron-up"></i> Hide details';
    });

    body.appendChild(toggle);
    body.appendChild(detailsDiv);

    stepDiv.appendChild(body);

    container.appendChild(stepDiv);

  });

}

function renderStepDetails(details) {

  if (!details || typeof details !== "object") {
    return '<span class="text-gray-500 text-sm">No details.</span>';
  }

  let html = '<div class="space-y-1">';

  Object.entries(details).forEach(([key, value]) => {

    html += `
      <div class="flex justify-between text-sm">
        <span class="font-medium text-gray-700">
        ${key.replace(/_/g, " ")}:
        </span>
        <span class="text-gray-600">${JSON.stringify(value)}</span>
      </div>
    `;

  });

  html += "</div>";

  return html;

}

/* ---------------------------------------------------
   Main Audit UI
--------------------------------------------------- */

function initAuditResults() {

  const auditTableBody = document.querySelector("#audit-table tbody");
  const violationsTableBody = document.querySelector("#violations-table tbody");

  const risksList = document.getElementById("risks-list");
  const recommendationsList = document.getElementById("recommendations-list");

  const scoreValue = document.getElementById("score-value");
  const scoreCircle = document.querySelector(".progress-circle");

  const statusBadge = document.getElementById("status-badge");
  const scoreBadge = document.getElementById("score-badge");
  const violationsStatusBadge = document.getElementById("violations-status-badge");
  const rulesCountField = document.getElementById("rules-count");
  const riskValueField = document.getElementById("risk-value");
  const violationsCount = document.getElementById("violations-count");
  const riskLevelBadge = document.getElementById("risk-level-badge");

  const documentField = document.getElementById("audit-document");
  const standardField = document.getElementById("audit-standard");
  const createdAtField = document.getElementById("audit-created-at");

  const violationsSummary = document.getElementById("violations-summary");
  const evidenceList = document.getElementById("evidence-list");
  const keywordList = document.getElementById("keyword-list");

  const loadingOverlay = document.getElementById("audit-loading");
  const lastUpdated = document.getElementById("last-updated");


/* ---------------------------------------------------
   Score
--------------------------------------------------- */

  const setScore = (score = 0) => {

    if (scoreValue) scoreValue.innerText = `${score}%`;

    if (scoreBadge) {
      const label =
        score >= 90 ? "Excellent" :
        score >= 75 ? "Good" :
        score >= 50 ? "Fair" :
        "Needs improvement";

      scoreBadge.textContent = label;
      scoreBadge.className =
        score >= 75 ? "badge badge--success" :
        score >= 50 ? "badge badge--warning" :
        "badge badge--danger";
    }

    if (!scoreCircle) return;

    const rotation = (score / 100) * 360;

    scoreCircle.style.setProperty("--progress", `${rotation}deg`);

    const scoreClass =
      score >= 80 ? "success" :
      score >= 50 ? "warning" :
      "danger";

    scoreCircle.classList.remove(
      "score-success",
      "score-warning",
      "score-danger"
    );

    scoreCircle.classList.add(`score-${scoreClass}`);

  };


/* ---------------------------------------------------
   Compliance Status
--------------------------------------------------- */

  const setComplianceStatus = (status = "unknown") => {

    if (!statusBadge) return;

    const mappings = {
      compliant: { text: "Compliant", class: "badge badge--success" },
      partially_compliant: { text: "Partial", class: "badge badge--warning" },
      non_compliant: { text: "Non-Compliant", class: "badge badge--danger" },
    };

    const info = mappings[status] || { text: "Unknown", class: "badge badge--info" };
    statusBadge.textContent = info.text;
    statusBadge.className = info.class;

  };

  const setViolationsSummary = (violations = []) => {
    if (!violationsSummary) return;

    const count = violations.length;
    violationsSummary.textContent = `${count} issue${count === 1 ? "" : "s"} detected`;

    if (violationsStatusBadge) {
      if (count === 0) {
        violationsStatusBadge.textContent = "None";
        violationsStatusBadge.className = "badge badge--success";
      } else if (count <= 3) {
        violationsStatusBadge.textContent = "Low";
        violationsStatusBadge.className = "badge badge--warning";
      } else {
        violationsStatusBadge.textContent = "High";
        violationsStatusBadge.className = "badge badge--danger";
      }
    }

    if (rulesCountField) {
      rulesCountField.textContent = `${count}`;
    }
  };


/* ---------------------------------------------------
   Risk Level
--------------------------------------------------- */

  const setRiskLevel = (violations = []) => {

    if (!riskLevelBadge) return;

    let text = "Low";
    let badgeClass = "badge badge--success";

    if (violations.length > 10) {
      text = "High";
      badgeClass = "badge badge--danger";
    } else if (violations.length > 5) {
      text = "Medium";
      badgeClass = "badge badge--warning";
    }

    riskLevelBadge.textContent = text;
    riskLevelBadge.className = badgeClass;

    if (riskValueField) {
      riskValueField.textContent = text;
    }

  };


/* ---------------------------------------------------
   Violations
--------------------------------------------------- */

  const renderViolations = (violations = []) => {

    if (!violationsTableBody) return;

    violationsTableBody.innerHTML = "";

    if (!violations.length) {

      violationsTableBody.innerHTML =
        '<tr><td colspan="5" class="text-center text-gray-500 py-6">No violations found</td></tr>';

      return;

    }

    violations.forEach((violation) => {

      const tr = document.createElement("tr");

      tr.className = "border-b border-gray-100";

      const requirement = violation.description || violation.rule_id || violation.summary || "Unknown";
      const status = violation.status || "unknown";
      const severity = violation.severity || "medium";
      let evidence = "";
      if (Array.isArray(violation.evidence)) {
        evidence = violation.evidence
          .map((item) => {
            if (typeof item === "string") return item;
            if (item && typeof item === "object") {
              return (
                item.sentence ||
                item.text ||
                item.chunk_text ||
                item.evidence_used ||
                ""
              );
            }
            return "";
          })
          .filter(Boolean)
          .join(" \n");
      }
      const recommendation = violation.reason || violation.reasoning || "";

      tr.innerHTML = `
        <td class="px-4 py-3">${requirement}</td>
        <td class="px-4 py-3 capitalize">${status}</td>
        <td class="px-4 py-3 capitalize">${severity}</td>
        <td class="px-4 py-3 whitespace-pre-line text-xs text-gray-700">${evidence || "--"}</td>
        <td class="px-4 py-3 text-xs text-gray-700">${recommendation || "--"}</td>
      `;

      violationsTableBody.appendChild(tr);

    });

  };

  const renderEvidence = (violations = []) => {
    if (!evidenceList) return;

    const snippets = [];

    violations.forEach((violation) => {
      if (Array.isArray(violation.evidence)) {
        violation.evidence.forEach((item) => {
          let text = "";
          if (typeof item === "string") {
            text = item;
          } else if (item && typeof item === "object") {
            text =
              item.sentence ||
              item.text ||
              item.chunk_text ||
              item.evidence_used ||
              "";
          }
          if (text && text.trim()) {
            snippets.push({
              rule: violation.rule_id || violation.description || "",
              text: text.trim(),
            });
          }
        });
      }
    });

    evidenceList.innerHTML = "";

    if (!snippets.length) {
      const placeholder = document.createElement("div");
      placeholder.className = "rounded-lg border border-dashed border-gray-200 p-6 text-center text-gray-500";
      placeholder.textContent = "No evidence available.";
      evidenceList.appendChild(placeholder);
      return;
    }

    snippets.slice(0, 6).forEach((snippet) => {
      const card = document.createElement("div");
      card.className = "rounded-lg border border-gray-200 p-4 bg-gray-50";

      const header = document.createElement("div");
      header.className = "flex items-center justify-between text-xs font-semibold text-gray-600";
      header.innerHTML = `
        <span>${snippet.rule || "Requirement"}</span>
        <span class="text-gray-500">Evidence</span>
      `;

      const body = document.createElement("p");
      body.className = "mt-2 text-sm text-gray-700 whitespace-pre-line";
      body.textContent = snippet.text;

      card.appendChild(header);
      card.appendChild(body);
      evidenceList.appendChild(card);
    });
  };


/* ---------------------------------------------------
   Generic Lists
--------------------------------------------------- */

  const renderList = (container, items = [], emptyLabel = "None") => {

    if (!container) return;

    container.innerHTML = "";

    if (!items.length) {

      const li = document.createElement("li");
      li.textContent = emptyLabel;
      li.className = "text-gray-500 text-sm";

      container.appendChild(li);
      return;

    }

    items.forEach((item) => {

      const li = document.createElement("li");
      li.textContent = item;

      container.appendChild(li);

    });

  };


/* ---------------------------------------------------
   Audit Details
--------------------------------------------------- */

  const renderAuditDetails = (audit) => {

    const score = audit.score || 0;
    const status = (audit.status || "unknown").toLowerCase();
    const violations = audit.violation_details || audit.violations || [];
    const risks = audit.risks || [];
    const recommendations = audit.recommendations || [];

    setScore(score);
    setComplianceStatus(status);
    setRiskLevel(violations);
    setViolationsSummary(violations);

    renderViolations(violations);
    renderEvidence(violations);
    renderList(keywordList, audit.detected_keywords || [], "No keywords detected.");
    renderList(risksList, risks);
    renderList(recommendationsList, recommendations);

    if (violationsCount) {
      violationsCount.textContent = violations.length;
    }

    if (documentField) {
      documentField.textContent = audit.document_name || "-";
    }

    if (standardField) {
      standardField.textContent = audit.standard_name || "-";
    }

    if (createdAtField) {
      const created = audit.created_at
        ? new Date(audit.created_at).toLocaleString()
        : "-";

      createdAtField.textContent = created;
    }

    renderAuditPipeline(audit.steps || []);

  };


/* ---------------------------------------------------
   Audit Table
--------------------------------------------------- */

  const fillAuditTable = (audits) => {

    if (!auditTableBody) return;

    auditTableBody.innerHTML = "";

    audits.forEach((audit) => {

      const tr = document.createElement("tr");

      tr.className =
        "hover:bg-gray-50 cursor-pointer border-b border-gray-100";

      const name = (audit.document_name || "Unknown")
        .split("/")
        .pop();

      const score = audit.score || 0;

      const status = (audit.status || "unknown").toLowerCase();
      const statusLabel =
        status === "compliant" ? "Compliant" :
        status === "partially_compliant" ? "Partial" :
        status === "non_compliant" ? "Non-Compliant" :
        "Unknown";

      tr.innerHTML = `
        <td class="px-6 py-4">${name}</td>
        <td class="px-6 py-4">${audit.standard_name || "-"}</td>
        <td class="px-6 py-4 font-semibold">${score}</td>
        <td class="px-6 py-4">${statusLabel}</td>
        <td class="px-6 py-4">${audit.created_at ?
          new Date(audit.created_at).toLocaleDateString() : "-"}</td>
      `;

      tr.addEventListener("click", () => {

        document
          .querySelectorAll("#audit-table tbody tr")
          .forEach((row) => row.classList.remove("bg-sky-50"));

        tr.classList.add("bg-sky-50");

        renderAuditDetails(audit);

      });

      auditTableBody.appendChild(tr);

    });

  };


/* ---------------------------------------------------
   Loading
--------------------------------------------------- */

  const setLoading = (loading) => {
    if (!loadingOverlay) return;
    loadingOverlay.style.display = loading ? "flex" : "none";
  };

  const setLastUpdated = () => {
    if (!lastUpdated) return;
    lastUpdated.textContent = new Date().toLocaleString();
  };


/* ---------------------------------------------------
   Load Results
--------------------------------------------------- */

  const loadAuditResults = async () => {

    setLoading(true);

    try {

      const res = await fetch(auditResultsEndpoint);

      if (!res.ok) return;

      const data = await res.json();
      
      const audits = data.results || data;

      if (!Array.isArray(audits) || audits.length === 0) {
        if (auditTableBody) {
            auditTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-gray-500 py-6">No audits found</td></tr>';
        }
        return;
      }

      fillAuditTable(audits);

      renderAuditDetails(audits[0]);

      const first = auditTableBody.querySelector("tr");
      if (first) first.classList.add("bg-sky-50");

      setLastUpdated();

    } catch (err) {

      console.error("Audit load failed:", err);

    } finally {

      setLoading(false);

    }

  };


/* ---------------------------------------------------
   Refresh
--------------------------------------------------- */

  const refreshBtn = document.getElementById("refresh-results");

  if (refreshBtn) {
    refreshBtn.addEventListener("click", loadAuditResults);
  }

  loadAuditResults();

}

window.initAuditResults = initAuditResults;