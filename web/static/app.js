// Self-Evolving AI Supply Chain Network - UI Controller & Interactive Engine
// Includes PostgreSQL Authentication, Session Management & Security Audit

let currentThreadId = null;
let graphData = { nodes: [], links: [] };
let canvas, ctx;
let nodePositions = {};
let isDragging = false;
let draggedNode = null;
let hoveredNode = null;

// User Authentication State
let currentUser = null;
let authToken = localStorage.getItem("sc_auth_token") || null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    initCanvas();
    initAuthSystem();
    fetchSystemStatus();
    fetchTopology();
    fetchSpotRates();
    fetchEvolution();
    fetchTelemetry();
    fetchAuditLogs();
    
    // Auto refresh telemetry, audit log and status every 2.5s
    setInterval(() => {
        fetchSystemStatus();
        fetchTelemetry();
        fetchSpotRates();
        fetchEvolution();
        fetchAuditLogs();
    }, 2500);

    setupEventListeners();
});

// -----------------------------------------------------------------------------
// PostgreSQL Authentication & User Session Management
// -----------------------------------------------------------------------------
async function initAuthSystem() {
    setupAuthEventListeners();

    if (authToken) {
        try {
            const res = await fetch("/api/auth/me", {
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAuthenticatedUser(data.user);
            } else {
                clearAuthSession();
            }
        } catch (e) {
            console.error("Auth validation error", e);
            clearAuthSession();
        }
    } else {
        // Auto sign-in demo operator for immediate zero-friction showcase if not signed in
        autoSignInDefaultDemo();
    }
}

async function autoSignInDefaultDemo() {
    try {
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: "operator", password: "operator123" })
        });
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem("sc_auth_token", data.token);
            authToken = data.token;
            setAuthenticatedUser(data.user);
            addTerminalLog(`[POSTGRES_AUTH] Connected as ${data.user.full_name} (${data.user.role.toUpperCase()}) via PostgreSQL`, "success");
        }
    } catch (e) {
        console.debug("Demo auto-login skipped", e);
    }
}

function setAuthenticatedUser(user) {
    currentUser = user;
    const unloggedEl = document.getElementById("auth-unlogged");
    const loggedEl = document.getElementById("auth-logged");
    
    if (unloggedEl && loggedEl) {
        unloggedEl.style.display = "none";
        loggedEl.style.display = "flex";
        
        document.getElementById("user-name").innerText = user.full_name || user.username;
        document.getElementById("user-role").innerText = (user.role || "OPERATOR").toUpperCase();
        
        const avatar = document.getElementById("user-avatar");
        if (avatar) {
            avatar.src = user.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${user.username}`;
        }
    }
}

function clearAuthSession() {
    currentUser = null;
    authToken = null;
    localStorage.removeItem("sc_auth_token");
    
    const unloggedEl = document.getElementById("auth-unlogged");
    const loggedEl = document.getElementById("auth-logged");
    if (unloggedEl && loggedEl) {
        unloggedEl.style.display = "block";
        loggedEl.style.display = "none";
    }
}

function setupAuthEventListeners() {
    const modal = document.getElementById("auth-modal");
    const btnOpen = document.getElementById("btn-open-signin");
    const btnClose = document.getElementById("btn-close-auth-modal");
    const btnLogout = document.getElementById("btn-logout");
    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const formLogin = document.getElementById("form-login");
    const formRegister = document.getElementById("form-register");
    const authAlert = document.getElementById("auth-alert");

    if (btnOpen && modal) {
        btnOpen.addEventListener("click", () => {
            modal.style.display = "flex";
            authAlert.style.display = "none";
        });
    }

    if (btnClose && modal) {
        btnClose.addEventListener("click", () => {
            modal.style.display = "none";
        });
    }

    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) modal.style.display = "none";
        });
    }

    if (btnLogout) {
        btnLogout.addEventListener("click", async () => {
            try {
                if (authToken) {
                    await fetch("/api/auth/logout", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ token: authToken })
                    });
                }
            } catch (e) {
                console.error("Logout error", e);
            }
            clearAuthSession();
            addTerminalLog("[AUTH] Signed out of PostgreSQL session.", "warn");
        });
    }

    // Tabs
    if (tabLogin && tabRegister) {
        tabLogin.addEventListener("click", () => {
            tabLogin.classList.add("active");
            tabRegister.classList.remove("active");
            formLogin.style.display = "flex";
            formRegister.style.display = "none";
            authAlert.style.display = "none";
        });

        tabRegister.addEventListener("click", () => {
            tabRegister.classList.add("active");
            tabLogin.classList.remove("active");
            formLogin.style.display = "none";
            formRegister.style.display = "flex";
            authAlert.style.display = "none";
        });
    }

    // Demo Account Buttons
    document.querySelectorAll(".demo-user-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const u = btn.getAttribute("data-user");
            const p = btn.getAttribute("data-pwd");
            document.getElementById("login-username").value = u;
            document.getElementById("login-password").value = p;
            tabLogin.click();
            formLogin.dispatchEvent(new Event("submit"));
        });
    });

    // Handle Login Submit
    if (formLogin) {
        formLogin.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("login-username").value.trim();
            const password = document.getElementById("login-password").value;
            const submitBtn = document.getElementById("btn-submit-login");

            submitBtn.disabled = true;
            submitBtn.innerText = "Authenticating with PostgreSQL...";

            try {
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                const data = await res.json();
                if (res.ok) {
                    localStorage.setItem("sc_auth_token", data.token);
                    authToken = data.token;
                    setAuthenticatedUser(data.user);
                    modal.style.display = "none";
                    addTerminalLog(`[POSTGRES_AUTH] Successfully logged in as ${data.user.full_name} (${data.user.role.toUpperCase()})`, "success");
                    fetchAuditLogs();
                } else {
                    showAuthAlert(data.detail || "Authentication failed. Check your credentials.", "error");
                }
            } catch (err) {
                showAuthAlert("Network connection error to PostgreSQL server.", "error");
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = "<span>🔐</span> Sign In via PostgreSQL";
            }
        });
    }

    // Handle Register Submit
    if (formRegister) {
        formRegister.addEventListener("submit", async (e) => {
            e.preventDefault();
            const full_name = document.getElementById("reg-fullname").value.trim();
            const username = document.getElementById("reg-username").value.trim();
            const role = document.getElementById("reg-role").value;
            const email = document.getElementById("reg-email").value.trim();
            const password = document.getElementById("reg-password").value;
            const submitBtn = document.getElementById("btn-submit-register");

            submitBtn.disabled = true;
            submitBtn.innerText = "Registering into PostgreSQL...";

            try {
                const res = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ full_name, username, role, email, password })
                });

                const data = await res.json();
                if (res.ok) {
                    localStorage.setItem("sc_auth_token", data.token);
                    authToken = data.token;
                    setAuthenticatedUser(data.user);
                    modal.style.display = "none";
                    addTerminalLog(`[POSTGRES_REGISTER] Registered new operator account: ${data.user.username} (${data.user.role})`, "success");
                    fetchAuditLogs();
                } else {
                    showAuthAlert(data.detail || "Registration failed. Username or email may already be taken.", "error");
                }
            } catch (err) {
                showAuthAlert("Network connection error to PostgreSQL server.", "error");
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = "<span>✨</span> Register into PostgreSQL";
            }
        });
    }

    const btnRefreshAudit = document.getElementById("btn-refresh-audit");
    if (btnRefreshAudit) {
        btnRefreshAudit.addEventListener("click", fetchAuditLogs);
    }
}

function showAuthAlert(msg, type = "error") {
    const alertEl = document.getElementById("auth-alert");
    if (alertEl) {
        alertEl.className = `auth-alert ${type}`;
        alertEl.innerText = msg;
        alertEl.style.display = "block";
    }
}

async function fetchAuditLogs() {
    const auditTerm = document.getElementById("auth-audit-terminal");
    if (!auditTerm) return;

    try {
        const res = await fetch("/api/auth/audit-log?limit=15");
        const data = await res.json();
        const logs = data.audit_logs || [];

        if (logs.length > 0) {
            auditTerm.innerHTML = "";
            logs.forEach(l => {
                const div = document.createElement("div");
                const timeStr = l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : "";
                const userStr = l.username || "Anonymous";
                const action = l.action;

                let colorClass = "info";
                if (action === "LOGIN" || action === "REGISTER") colorClass = "success";
                if (action === "FAILED_LOGIN") colorClass = "error";
                if (action === "HITL_APPROVED" || action === "SIMULATION_TRIGGERED") colorClass = "warn";

                div.className = `terminal-line ${colorClass}`;
                div.innerText = `[${timeStr}] [POSTGRES_AUDIT] Action: ${action} | User: ${userStr} | IP: ${l.ip_address || '127.0.0.1'}`;
                auditTerm.appendChild(div);
            });
        }
    } catch (e) {
        console.debug("Audit log fetch error", e);
    }
}

// -----------------------------------------------------------------------------
// General UI & Event Listeners
// -----------------------------------------------------------------------------
function setupEventListeners() {
    document.getElementById("btn-trigger-suez").addEventListener("click", () => {
        triggerDisruption("GEOPOLITICAL_DISRUPTION", "COR_SUEZ_REDSEA", "Maritime chokepoint shutdown & drone risk");
    });

    document.getElementById("btn-trigger-wafer").addEventListener("click", () => {
        triggerDisruption("MARKET_SHIFT_ANOMALY", "COR_TRANSPACIFIC", "Lithium and Silicon wafer spot price spike +55%");
    });

    document.getElementById("btn-stream-telemetry").addEventListener("click", startStreaming);
    
    document.getElementById("btn-approve-hitl").addEventListener("click", () => {
        submitHitlDecision(true);
    });

    document.getElementById("btn-reject-hitl").addEventListener("click", () => {
        submitHitlDecision(false);
    });

    // Guardrail policy sliders
    const sliderSpend = document.getElementById("slider-spend-cap");
    const sliderRisk = document.getElementById("slider-risk-thresh");
    const sliderMarkup = document.getElementById("slider-markup-cap");

    if (sliderSpend) {
        sliderSpend.addEventListener("input", (e) => {
            document.getElementById("val-spend-cap").innerText = `$${parseInt(e.target.value).toLocaleString()}`;
        });
        sliderSpend.addEventListener("change", syncGuardrailPolicies);
    }

    if (sliderRisk) {
        sliderRisk.addEventListener("input", (e) => {
            document.getElementById("val-risk-thresh").innerText = `${e.target.value} / 100`;
        });
        sliderRisk.addEventListener("change", syncGuardrailPolicies);
    }

    if (sliderMarkup) {
        sliderMarkup.addEventListener("input", (e) => {
            document.getElementById("val-markup-cap").innerText = `+${e.target.value}%`;
        });
        sliderMarkup.addEventListener("change", syncGuardrailPolicies);
    }
}

async function syncGuardrailPolicies() {
    const spend = parseFloat(document.getElementById("slider-spend-cap").value);
    const risk = parseFloat(document.getElementById("slider-risk-thresh").value);
    const markup = parseFloat(document.getElementById("slider-markup-cap").value);

    try {
        const headers = { "Content-Type": "application/json" };
        if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

        await fetch("/api/guardrails/update", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
                max_contract_usd: spend,
                max_rate_premium: markup,
                risk_threshold: risk
            })
        });
        addTerminalLog(`[POLICY_SYNC] Operational guardrails updated: SpendCap=$${spend.toLocaleString()}, RiskThresh=${risk}, MarkupCap=${markup}%`, "warn");
    } catch (e) {
        console.error("Failed to update guardrails", e);
    }
}

// -----------------------------------------------------------------------------
// Canvas Interactive Tier-N Knowledge Graph
// -----------------------------------------------------------------------------
function initCanvas() {
    canvas = document.getElementById("graph-canvas");
    if (!canvas) return;
    ctx = canvas.getContext("2d");

    function resize() {
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = 360;
        layoutNodes();
    }
    window.addEventListener("resize", resize);
    resize();

    canvas.addEventListener("mousedown", onMouseDown);
    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("mouseup", onMouseUp);

    requestAnimationFrame(renderGraphLoop);
}

function layoutNodes() {
    if (!canvas || !graphData.nodes || graphData.nodes.length === 0) return;
    const w = canvas.width;
    const h = canvas.height;

    const layers = {
        Enterprise: [],
        Tier1_Supplier: [],
        Tier2_Supplier: [],
        Tier3_Supplier: [],
        Corridor: [],
        Component: []
    };

    graphData.nodes.forEach(n => {
        const group = n.group || "Tier1_Supplier";
        if (layers[group]) layers[group].push(n);
        else layers.Tier1_Supplier.push(n);
    });

    const layerOrder = ["Enterprise", "Tier1_Supplier", "Tier2_Supplier", "Tier3_Supplier"];
    const colWidth = w / (layerOrder.length + 1);

    layerOrder.forEach((layerKey, colIdx) => {
        const nodes = layers[layerKey] || [];
        const x = colWidth * (colIdx + 1);
        const rowHeight = h / (nodes.length + 1);

        nodes.forEach((node, rowIdx) => {
            if (!nodePositions[node.id]) {
                nodePositions[node.id] = {
                    id: node.id,
                    name: node.name,
                    group: node.group,
                    risk_score: node.risk_score || 20,
                    x: x,
                    y: rowHeight * (rowIdx + 1),
                    radius: node.group === "Enterprise" ? 22 : 16,
                    color: getNodeColor(node.group, node.risk_score)
                };
            }
        });
    });
}

function getNodeColor(group, risk) {
    if (risk && risk > 60) return "#ff3366";
    switch (group) {
        case "Enterprise": return "#00f2fe";
        case "Tier1_Supplier": return "#4facfe";
        case "Tier2_Supplier": return "#a855f7";
        case "Tier3_Supplier": return "#f9b208";
        default: return "#00f5a0";
    }
}

function renderGraphLoop() {
    if (!ctx || !canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw Links
    if (graphData.links) {
        graphData.links.forEach(l => {
            const src = nodePositions[l.source];
            const tgt = nodePositions[l.target];
            if (src && tgt) {
                ctx.beginPath();
                ctx.moveTo(src.x, src.y);
                ctx.lineTo(tgt.x, tgt.y);
                ctx.strokeStyle = "rgba(64, 120, 224, 0.35)";
                ctx.lineWidth = 1.5;
                ctx.stroke();

                // Animated glowing data particle
                const t = (Date.now() % 2000) / 2000;
                const px = src.x + (tgt.x - src.x) * t;
                const py = src.y + (tgt.y - src.y) * t;
                ctx.beginPath();
                ctx.arc(px, py, 3, 0, Math.PI * 2);
                ctx.fillStyle = "#00f2fe";
                ctx.shadowColor = "#00f2fe";
                ctx.shadowBlur = 8;
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        });
    }

    // Draw Nodes
    for (let id in nodePositions) {
        const p = nodePositions[id];
        const isHovered = hoveredNode === id;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = isHovered ? 16 : 8;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = isHovered ? 2.5 : 1;
        ctx.stroke();

        ctx.fillStyle = "#f0f4fc";
        ctx.font = isHovered ? "bold 11px Outfit, sans-serif" : "10px Outfit, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(p.name, p.x, p.y + p.radius + 14);
    }

    requestAnimationFrame(renderGraphLoop);
}

function onMouseDown(e) {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    for (let id in nodePositions) {
        const p = nodePositions[id];
        const dist = Math.hypot(p.x - mx, p.y - my);
        if (dist <= p.radius) {
            isDragging = true;
            draggedNode = p;
            break;
        }
    }
}

function onMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (isDragging && draggedNode) {
        draggedNode.x = mx;
        draggedNode.y = my;
        return;
    }

    hoveredNode = null;
    for (let id in nodePositions) {
        const p = nodePositions[id];
        if (Math.hypot(p.x - mx, p.y - my) <= p.radius) {
            hoveredNode = id;
            canvas.style.cursor = "pointer";
            return;
        }
    }
    canvas.style.cursor = "default";
}

function onMouseUp() {
    isDragging = false;
    draggedNode = null;
}

// -----------------------------------------------------------------------------
// API Integration Calls
// -----------------------------------------------------------------------------
async function fetchSystemStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        
        document.getElementById("stat-gen").innerText = `Gen ${data.evolution_generation}`;
        document.getElementById("kpi-gen").innerText = `v${data.evolution_generation}.0`;
        document.getElementById("kpi-runs").innerText = data.active_workflow_runs;

        const statPostgres = document.getElementById("stat-postgres");
        const statPostgresDot = document.getElementById("stat-postgres-dot");
        const backendTag = document.getElementById("auth-backend-tag");

        if (statPostgres && statPostgresDot) {
            if (data.postgres_connected) {
                statPostgresDot.className = "status-dot active";
                statPostgres.innerText = "PostgreSQL (Connected)";
            } else {
                statPostgresDot.className = "status-dot active";
                statPostgres.innerText = `Auth (${data.auth_backend || 'Active'})`;
            }
        }

        if (backendTag) {
            backendTag.innerText = data.postgres_connected ? "PostgreSQL Engine: ONLINE" : `Auth Engine: ${data.auth_backend || 'Ready'}`;
        }
    } catch (e) {
        console.error("Status fetch error", e);
    }
}

async function fetchTopology() {
    try {
        const res = await fetch("/api/topology");
        graphData = await res.json();
        layoutNodes();
    } catch (e) {
        console.error("Topology fetch error", e);
    }
}

async function fetchSpotRates() {
    try {
        const res = await fetch("/api/spot-rates");
        const data = await res.json();
        if (data.corridors && data.corridors.length > 0) {
            const suez = data.corridors[0];
            const rateEl = document.getElementById("kpi-suez-rate");
            const spikeEl = document.getElementById("kpi-suez-spike");
            if (rateEl) rateEl.innerText = `$${suez.current_spot_usd.toLocaleString()}`;
            if (spikeEl) {
                spikeEl.innerText = `+${suez.surge_percentage}% vs baseline (Z-Score: ${suez.z_score})`;
            }
        }
    } catch (e) {
        console.error("Spot rate fetch error", e);
    }
}

async function fetchEvolution() {
    try {
        const res = await fetch("/api/evolution");
        const data = await res.json();
        const weights = data.adaptive_heuristic_weights || {};

        if (document.getElementById("w-reliability")) {
            document.getElementById("w-reliability").innerText = weights.supplier_reliability_weight?.toFixed(2) || "0.45";
            document.getElementById("w-cost").innerText = weights.cost_minimization_weight?.toFixed(2) || "0.35";
            document.getElementById("w-speed").innerText = weights.transit_speed_weight?.toFixed(2) || "0.20";
            document.getElementById("w-risk-thresh").innerText = `${data.adaptive_risk_threshold?.toFixed(1) || 65.0}/100`;
        }

        const lessonsDiv = document.getElementById("evolution-lessons");
        if (lessonsDiv && data.episodic_lessons_learned) {
            lessonsDiv.innerHTML = "";
            data.episodic_lessons_learned.forEach(l => {
                const div = document.createElement("div");
                div.className = "terminal-line info";
                div.innerText = `🧬 [Gen ${data.generation}] ${l}`;
                lessonsDiv.appendChild(div);
            });
        }
    } catch (e) {
        console.error("Evolution fetch error", e);
    }
}

async function fetchTelemetry() {
    try {
        const res = await fetch("/api/telemetry");
        const data = await res.json();
        const ledger = data.audit_ledger || [];

        const feed = document.getElementById("live-audit-feed");
        if (feed && ledger.length > 0) {
            feed.innerHTML = "";
            ledger.forEach(item => {
                const div = document.createElement("div");
                div.className = `ledger-item ${item.decision.toLowerCase()}`;
                div.innerHTML = `
                    <div class="ledger-header">
                        <span class="ledger-tag">${item.decision}</span>
                        <span class="ledger-time">${item.timestamp}</span>
                    </div>
                    <div class="ledger-body">${item.description}</div>
                    <div class="ledger-footer">
                        <span>Cost: $${(item.cost_usd || 0).toLocaleString()}</span>
                        <span>Corridor: ${item.corridor_id}</span>
                    </div>
                `;
                feed.appendChild(div);
            });
        }
    } catch (e) {
        console.error("Telemetry fetch error", e);
    }
}

async function triggerDisruption(triggerType, corridorId, reason) {
    try {
        addTerminalLog(`[TRIGGER_SIMULATION] Launching disruption event: ${triggerType} on ${corridorId}...`, "warn");
        const headers = { "Content-Type": "application/json" };
        if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

        const res = await fetch("/api/trigger", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
                trigger_type: triggerType,
                corridor_id: corridorId,
                target_id: corridorId,
                severity: "CRITICAL",
                reason: reason,
                spike_pct: 68.0
            })
        });
        const data = await res.json();
        currentThreadId = data.thread_id;
        addTerminalLog(`[LANGGRAPH_EXEC] Thread checkpointed: ${currentThreadId} (HITL: ${data.hitl_status})`, "info");
        updateAgentFlowUI(data.result);
        fetchEvolution();
        fetchAuditLogs();
    } catch (e) {
        addTerminalLog(`Error triggering disruption: ${e}`, "error");
    }
}

async function submitHitlDecision(approved) {
    if (!currentThreadId) {
        alert("No active paused workflow awaiting HITL approval.");
        return;
    }
    try {
        const userName = currentUser ? currentUser.full_name : "Executive Supply Chain Officer";
        addTerminalLog(`[HITL_GATE] Recording decision by ${userName}: ${approved ? 'APPROVED' : 'REJECTED'}`, "warn");

        const headers = { "Content-Type": "application/json" };
        if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

        const res = await fetch("/api/hitl/decision", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
                thread_id: currentThreadId,
                approved: approved,
                feedback: approved ? `Authorized by ${userName}` : `Rejected by ${userName}`
            })
        });
        const data = await res.json();
        updateAgentFlowUI(data.result);
        fetchEvolution();
        fetchAuditLogs();
    } catch (e) {
        addTerminalLog(`Error recording HITL decision: ${e}`, "error");
    }
}

async function startStreaming() {
    try {
        addTerminalLog("[KAFKA_STREAM] Started high-frequency container telemetry stream burst.", "info");
        await fetch("/api/stream/start", { method: "POST" });
    } catch (e) {
        console.error(e);
    }
}

function updateAgentFlowUI(state) {
    if (!state) return;

    // 1. Market Intel Node
    const intel = state.market_intelligence || {};
    const nIntel = document.getElementById("node-intel");
    if (nIntel) {
        nIntel.className = "agent-node-card success";
        document.getElementById("node-intel-status").innerText = `Shift: +${intel.spike_percentage || 0}%`;
    }

    // 2. Graph Traversal Node
    const blast = state.graph_blast_radius || {};
    const nGraph = document.getElementById("node-graph");
    if (nGraph) {
        nGraph.className = "agent-node-card success";
        document.getElementById("node-graph-status").innerText = `Jeopardized: $${(blast.jeopardized_contract_usd || 0).toLocaleString()}`;
    }

    // 3. Negotiator Node
    const proposal = state.selected_proposal || {};
    const nNeg = document.getElementById("node-negotiator");
    if (nNeg) {
        nNeg.className = "agent-node-card success";
        document.getElementById("node-negotiator-status").innerText = `Switch: ${proposal.alternative_supplier_name || 'US Backup'}`;
    }

    // 4. Guardrails & HITL Banner
    const isHitl = state.hitl_status === "PENDING_APPROVAL";
    const hitlBanner = document.getElementById("hitl-banner");
    const nHitl = document.getElementById("node-hitl");

    if (isHitl) {
        hitlBanner.style.display = "flex";
        document.getElementById("hitl-desc").innerText = 
            `Contract amendment with ${proposal.alternative_supplier_name} exceeds autonomous threshold ($${(proposal.estimated_cost_usd || 0).toLocaleString()} USD). Policy mandates human executive sign-off.`;
        if (nHitl) {
            nHitl.className = "agent-node-card hitl-halt";
            document.getElementById("node-hitl-status").innerText = "PAUSED (Awaiting Human)";
        }
    } else {
        hitlBanner.style.display = "none";
        if (nHitl) {
            nHitl.className = "agent-node-card success";
            document.getElementById("node-hitl-status").innerText = state.hitl_status || "PASSED";
        }
    }

    // 5. Evolution Node
    const evo = state.evolution_metrics || {};
    const nEvo = document.getElementById("node-evolution");
    if (nEvo && evo.generation) {
        nEvo.className = "agent-node-card success";
        document.getElementById("node-evolution-status").innerText = `Gen ${evo.generation} (+${evo.reward_score} reward)`;
    }

    // Update terminal with agent execution logs
    if (state.logs) {
        state.logs.forEach(l => addTerminalLog(l, "info"));
    }
}

function addTerminalLog(msg, type = "info") {
    const term = document.getElementById("live-terminal");
    if (!term) return;
    const div = document.createElement("div");
    div.className = `terminal-line ${type}`;
    div.innerText = msg;
    term.appendChild(div);
    term.scrollTop = term.scrollHeight;
}
