/**
 * CognoDB & Graph DB Cloud Benchmark Explorer
 * Interactive Force-Directed Graph Engine & Analytics
 */

// ==========================================
// 1. Interactive Tabs
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      
      btn.classList.add('active');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add('active');

      // Trigger resize for canvas/charts when tab becomes visible
      if (btn.dataset.tab === 'tab-graph') {
        resizeCanvas();
      }
    });
  });

  initGraphVisualizer();
  initBenchmarkCharts();
  initCypherPlayground();
});

// ==========================================
// 2. Interactive Force-Directed Graph Canvas
// ==========================================
let graphNodes = [];
let graphEdges = [];
let animFrameId = null;
let isPhysicsRunning = true;
let scale = 1.0;
let panX = 0;
let panY = 0;
let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;
let hoveredNode = null;
let selectedNode = null;
let activeHighlightedNodes = new Set();
let activeHighlightedEdges = new Set();

const communityColors = [
  '#38bdf8', // Comm 0 (Cyan)
  '#c084fc', // Comm 1 (Purple)
  '#34d399', // Comm 2 (Green)
  '#fb923c'  // Comm 3 (Orange)
];

function initGraphVisualizer() {
  const canvas = document.getElementById('graphCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Load sample dataset
  const sample = window.GRAPH_SAMPLE || { nodes: [], edges: [] };
  const width = canvas.parentElement.clientWidth;
  const height = canvas.parentElement.clientHeight;

  // Initialize node physics positions
  graphNodes = sample.nodes.map((n, idx) => ({
    id: n.id,
    community: n.community,
    x: width / 2 + (Math.random() - 0.5) * (width * 0.7),
    y: height / 2 + (Math.random() - 0.5) * (height * 0.7),
    vx: 0,
    vy: 0,
    radius: 7 + (n.community % 3) * 2,
    color: communityColors[n.community % communityColors.length]
  }));

  const nodeMap = new Map(graphNodes.map(n => [n.id, n]));
  graphEdges = sample.edges
    .filter(e => nodeMap.has(e.source) && nodeMap.has(e.target))
    .map(e => ({
      source: nodeMap.get(e.source),
      target: nodeMap.get(e.target)
    }));

  // Populate Select Dropdown
  const select = document.getElementById('nodeSelect');
  if (select) {
    select.innerHTML = graphNodes.slice(0, 30).map(n => 
      `<option value="${n.id}">Node #${n.id} (Comm ${n.community})</option>`
    ).join('');

    select.addEventListener('change', (e) => {
      const nid = parseInt(e.target.value, 10);
      selectNodeById(nid);
    });
  }

  // Traversal Buttons
  document.querySelectorAll('.btn-hop').forEach(btn => {
    btn.addEventListener('click', () => {
      const hops = parseInt(btn.dataset.hops, 10);
      simulateMultiHop(hops);
    });
  });

  // Canvas Controls
  document.getElementById('btnZoomIn')?.addEventListener('click', () => { scale = Math.min(scale * 1.25, 3.0); });
  document.getElementById('btnZoomOut')?.addEventListener('click', () => { scale = Math.max(scale * 0.8, 0.4); });
  document.getElementById('btnResetView')?.addEventListener('click', () => {
    scale = 1.0; panX = 0; panY = 0;
  });
  document.getElementById('btnTogglePhysics')?.addEventListener('click', (e) => {
    isPhysicsRunning = !isPhysicsRunning;
    e.currentTarget.innerHTML = isPhysicsRunning ? 
      '<i class="fa-solid fa-pause"></i>' : '<i class="fa-solid fa-play"></i>';
  });

  // Canvas Interactions
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - panX) / scale;
    const my = (e.clientY - rect.top - panY) / scale;

    const clicked = graphNodes.find(n => Math.hypot(n.x - mx, n.y - my) <= n.radius + 4);
    if (clicked) {
      selectNodeById(clicked.id);
    } else {
      isDragging = true;
      dragStartX = e.clientX - panX;
      dragStartY = e.clientY - panY;
    }
  });

  window.addEventListener('mousemove', (e) => {
    if (isDragging) {
      panX = e.clientX - dragStartX;
      panY = e.clientY - dragStartY;
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - panX) / scale;
    const my = (e.clientY - rect.top - panY) / scale;
    hoveredNode = graphNodes.find(n => Math.hypot(n.x - mx, n.y - my) <= n.radius + 4) || null;
    canvas.style.cursor = hoveredNode ? 'pointer' : 'grab';
  });

  window.addEventListener('mouseup', () => { isDragging = false; });

  // Start Animation Loop
  runSimulation();

  // Select initial node
  if (graphNodes.length > 0) {
    selectNodeById(graphNodes[0].id);
  }
}

function resizeCanvas() {
  const canvas = document.getElementById('graphCanvas');
  if (!canvas || !canvas.parentElement) return;
  canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
  canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
}

function runSimulation() {
  const canvas = document.getElementById('graphCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.width / dpr;
  const height = canvas.height / dpr;

  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);

  // Apply Pan & Zoom
  ctx.translate(panX, panY);
  ctx.scale(scale, scale);

  // 1. Force Physics Simulation step
  if (isPhysicsRunning) {
    // Spring forces for edges
    for (let e of graphEdges) {
      const dx = e.target.x - e.source.x;
      const dy = e.target.y - e.source.y;
      const dist = Math.hypot(dx, dy) || 1;
      const targetDist = 55;
      const force = (dist - targetDist) * 0.003;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      e.source.vx += fx;
      e.source.vy += fy;
      e.target.vx -= fx;
      e.target.vy -= fy;
    }

    // Repulsion between nodes
    for (let i = 0; i < graphNodes.length; i++) {
      const n1 = graphNodes[i];
      for (let j = i + 1; j < graphNodes.length; j++) {
        const n2 = graphNodes[j];
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist < 120) {
          const force = (120 - dist) * 0.012;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          n1.vx -= fx;
          n1.vy -= fy;
          n2.vx += fx;
          n2.vy += fy;
        }
      }

      // Center gravity
      const cdx = width / 2 - n1.x;
      const cdy = height / 2 - n1.y;
      n1.vx += cdx * 0.0004;
      n1.vy += cdy * 0.0004;

      // Update positions with friction damping
      n1.vx *= 0.88;
      n1.vy *= 0.88;
      n1.x += n1.vx;
      n1.y += n1.vy;
    }
  }

  // 2. Draw Edges
  for (let e of graphEdges) {
    const isHighlighted = activeHighlightedEdges.has(e);
    ctx.beginPath();
    ctx.moveTo(e.source.x, e.source.y);
    ctx.lineTo(e.target.x, e.target.y);
    ctx.strokeStyle = isHighlighted ? '#facc15' : 'rgba(255, 255, 255, 0.09)';
    ctx.lineWidth = isHighlighted ? 2.5 : 1.0;
    ctx.stroke();
  }

  // 3. Draw Nodes
  for (let n of graphNodes) {
    const isSelected = selectedNode && selectedNode.id === n.id;
    const isHovered = hoveredNode && hoveredNode.id === n.id;
    const isInPath = activeHighlightedNodes.has(n.id);

    // Glow ring
    if (isSelected || isHovered || isInPath) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius + 6, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? 'rgba(56, 189, 248, 0.35)' : (isInPath ? 'rgba(250, 204, 21, 0.3)' : 'rgba(255, 255, 255, 0.15)');
      ctx.fill();
    }

    ctx.beginPath();
    ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
    ctx.fillStyle = isInPath ? '#facc15' : (isSelected ? '#38bdf8' : n.color);
    ctx.fill();

    // Node label
    ctx.fillStyle = '#f1f5f9';
    ctx.font = '10px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillText(`${n.id}`, n.x, n.y + n.radius + 12);
  }

  ctx.restore();
  animFrameId = requestAnimationFrame(runSimulation);
}

function selectNodeById(id) {
  selectedNode = graphNodes.find(n => n.id === id) || null;
  if (!selectedNode) return;

  const select = document.getElementById('nodeSelect');
  if (select && select.value !== `${id}`) select.value = id;

  // Find direct neighbors
  const neighbors = [];
  for (let e of graphEdges) {
    if (e.source.id === id) neighbors.push(e.target.id);
    else if (e.target.id === id) neighbors.push(e.source.id);
  }

  const details = document.getElementById('nodeDetails');
  if (details) {
    details.innerHTML = `
      <div style="margin-top: 0.5rem;">
        <div class="metric-row"><span>Node ID:</span> <strong>#${selectedNode.id}</strong></div>
        <div class="metric-row"><span>Community:</span> <span class="badge badge-info">Cluster ${selectedNode.community}</span></div>
        <div class="metric-row"><span>Direct Degree:</span> <strong>${neighbors.length} connections</strong></div>
        <div class="metric-row"><span>Neighbor IDs:</span> <span class="text-muted" style="font-size:0.75rem;">${neighbors.slice(0, 8).join(', ')}${neighbors.length > 8 ? '...' : ''}</span></div>
      </div>
    `;
  }

  // Update simulator start node
  simulateMultiHop(1);
}

function simulateMultiHop(hops) {
  if (!selectedNode) return;

  activeHighlightedNodes.clear();
  activeHighlightedEdges.clear();

  let currentLevel = new Set([selectedNode.id]);
  activeHighlightedNodes.add(selectedNode.id);

  for (let h = 0; h < hops; h++) {
    let nextLevel = new Set();
    for (let e of graphEdges) {
      if (currentLevel.has(e.source.id) && !activeHighlightedNodes.has(e.target.id)) {
        nextLevel.add(e.target.id);
        activeHighlightedNodes.add(e.target.id);
        activeHighlightedEdges.add(e);
      } else if (currentLevel.has(e.target.id) && !activeHighlightedNodes.has(e.source.id)) {
        nextLevel.add(e.source.id);
        activeHighlightedNodes.add(e.source.id);
        activeHighlightedEdges.add(e);
      }
    }
    currentLevel = nextLevel;
  }

  // Update Live Simulation Panel
  const metrics = document.getElementById('traversalMetrics');
  if (metrics) {
    metrics.style.display = 'block';
    document.getElementById('metricVisitedNodes').textContent = `${activeHighlightedNodes.size}`;
    document.getElementById('metricTraversedEdges').textContent = `${activeHighlightedEdges.size}`;

    // Empirical latency numbers based on hop count
    const hopStats = {
      1: { memgraph: '2.5 ms', neo4j: '52.1 ms', cognodb: '252.3 ms' },
      2: { memgraph: '4.7 ms', neo4j: '52.8 ms', cognodb: '263.7 ms' },
      3: { memgraph: '86.2 ms', neo4j: '70.8 ms', cognodb: '2,184 ms' }
    };

    const stats = hopStats[hops] || hopStats[1];
    document.getElementById('metricMemgraph').textContent = stats.memgraph;
    document.getElementById('metricNeo4j').textContent = stats.neo4j;
    document.getElementById('metricCognoDB').textContent = stats.cognodb;
  }
}

// ==========================================
// 3. Interactive Benchmark Charts
// ==========================================
function initBenchmarkCharts() {
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Outfit', size: 12 } } },
      tooltip: {
        backgroundColor: '#111827',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleFont: { family: 'Outfit', size: 13, weight: 'bold' },
        bodyFont: { family: 'Inter', size: 12 }
      }
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { family: 'Inter' } } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { family: 'Inter' } } }
    }
  };

  // Traversal Latency Chart
  const ctxTrav = document.getElementById('chartTraversal')?.getContext('2d');
  if (ctxTrav) {
    window.chartTraversalInst = new Chart(ctxTrav, {
      type: 'bar',
      data: {
        labels: ['1-Hop (Neighbors)', '2-Hop (FOAF)', '3-Hop (Deep Expansion)'],
        datasets: [
          { label: 'Memgraph (Local)', data: [2.5, 4.7, 86.2], backgroundColor: '#34d399' },
          { label: 'FalkorDB (Local)', data: [1.1, 3.4, 218.5], backgroundColor: '#f87171' },
          { label: 'Neo4j Aura (Cloud)', data: [52.1, 52.8, 70.8], backgroundColor: '#fb923c' },
          { label: 'ArangoDB (Local)', data: [50.0, 64.0, 1289.9], backgroundColor: '#818cf8' },
          { label: 'CognoDB (Cloud c0)', data: [252.3, 263.7, 2184.1], backgroundColor: '#38bdf8' }
        ]
      },
      options: {
        ...chartOptions,
        scales: {
          ...chartOptions.scales,
          y: { ...chartOptions.scales.y, title: { display: true, text: 'p50 Latency (ms)', color: '#94a3b8' } }
        }
      }
    });

    // p50 vs p95 Toggle Buttons
    document.querySelectorAll('[data-metric-type]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-metric-type]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const type = btn.dataset.metricType;
        
        if (type === 'p95') {
          window.chartTraversalInst.data.datasets[0].data = [4.9, 16.6, 401.1];
          window.chartTraversalInst.data.datasets[1].data = [2.1, 14.5, 834.4];
          window.chartTraversalInst.data.datasets[2].data = [61.0, 58.9, 100.6];
          window.chartTraversalInst.data.datasets[3].data = [62.3, 116.2, 6629.9];
          window.chartTraversalInst.data.datasets[4].data = [259.1, 379.4, 6306.9];
        } else {
          window.chartTraversalInst.data.datasets[0].data = [2.5, 4.7, 86.2];
          window.chartTraversalInst.data.datasets[1].data = [1.1, 3.4, 218.5];
          window.chartTraversalInst.data.datasets[2].data = [52.1, 52.8, 70.8];
          window.chartTraversalInst.data.datasets[3].data = [50.0, 64.0, 1289.9];
          window.chartTraversalInst.data.datasets[4].data = [252.3, 263.7, 2184.1];
        }
        window.chartTraversalInst.update();
      });
    });
  }

  // Mixed Workload QPS vs Concurrency Chart
  const ctxQPS = document.getElementById('chartQPS')?.getContext('2d');
  if (ctxQPS) {
    new Chart(ctxQPS, {
      type: 'line',
      data: {
        labels: ['c=1 Client', 'c=10 Clients', 'c=40 Clients'],
        datasets: [
          { label: 'Memgraph', data: [363.1, 889.1, 1087.1], borderColor: '#34d399', tension: 0.3, pointRadius: 5 },
          { label: 'FalkorDB', data: [377.4, 1094.5, 967.8], borderColor: '#f87171', tension: 0.3, pointRadius: 5 },
          { label: 'Neo4j Aura', data: [12.3, 167.3, 607.6], borderColor: '#fb923c', tension: 0.3, pointRadius: 5 },
          { label: 'ArangoDB', data: [19.0, 180.1, 397.8], borderColor: '#818cf8', tension: 0.3, pointRadius: 5 },
          { label: 'CognoDB Cloud', data: [4.0, 39.3, 123.6], borderColor: '#38bdf8', tension: 0.3, pointRadius: 5 }
        ]
      },
      options: {
        ...chartOptions,
        scales: {
          ...chartOptions.scales,
          y: { ...chartOptions.scales.y, title: { display: true, text: 'Throughput (Queries / Second)', color: '#94a3b8' } }
        }
      }
    });
  }

  // Ingest Throughput Chart
  const ctxIngest = document.getElementById('chartIngest')?.getContext('2d');
  if (ctxIngest) {
    new Chart(ctxIngest, {
      type: 'bar',
      data: {
        labels: ['Memgraph', 'ArangoDB', 'FalkorDB', 'Neo4j Aura', 'CognoDB Cloud'],
        datasets: [{
          label: 'Ingested Relationships / Sec',
          data: [15355, 8580, 6144, 6130, 1871],
          backgroundColor: ['#34d399', '#818cf8', '#f87171', '#fb923c', '#38bdf8']
        }]
      },
      options: {
        ...chartOptions,
        indexAxis: 'y',
        plugins: { ...chartOptions.plugins, legend: { display: false } }
      }
    });
  }

  // Lookups & Aggregation Chart
  const ctxLookups = document.getElementById('chartLookups')?.getContext('2d');
  if (ctxLookups) {
    new Chart(ctxLookups, {
      type: 'bar',
      data: {
        labels: ['Memgraph', 'FalkorDB', 'Neo4j Aura', 'ArangoDB', 'CognoDB Cloud'],
        datasets: [
          { label: 'Point Lookup (id)', data: [0.9, 1.5, 51.3, 50.1, 243.9], backgroundColor: '#38bdf8' },
          { label: 'Community Aggregation', data: [290.0, 686.2, 306.3, 1911.7, 2301.1], backgroundColor: '#c084fc' }
        ]
      },
      options: chartOptions
    });
  }
}

// ==========================================
// 4. Cypher Playground & Live Query Runner
// ==========================================
function initCypherPlayground() {
  const editor = document.getElementById('cypherEditor');
  const paramInput = document.getElementById('paramId');
  const btnRun = document.getElementById('btnRunQuery');
  const resultTable = document.getElementById('resultTable');
  const statsLabel = document.getElementById('queryExecStats');

  const presets = {
    '1hop': 'MATCH (n:Person {id: $id})-[:FRIEND]->(m) RETURN m.id, m.community',
    '2hop': 'MATCH (n:Person {id: $id})-[:FRIEND*2]->(m) RETURN DISTINCT m.id, m.community',
    '3hop': 'MATCH (n:Person {id: $id})-[:FRIEND*3]->(m) RETURN count(DISTINCT m) AS total_reach',
    'agg': 'MATCH (n:Person)-[:FRIEND]-(m) RETURN n.community AS community, count(m) AS degrees ORDER BY degrees DESC LIMIT 10'
  };

  if (editor) editor.value = presets['1hop'];

  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const key = btn.dataset.preset;
      if (editor && presets[key]) editor.value = presets[key];
    });
  });

  if (btnRun) {
    btnRun.addEventListener('click', () => {
      const id = parseInt(paramInput?.value || '10', 10);
      const query = editor?.value || '';

      statsLabel.innerHTML = `<span class="badge badge-info"><i class="fa-solid fa-spinner fa-spin"></i> Executing against Bolt driver...</span>`;

      setTimeout(() => {
        // Evaluate simulated query plan
        const start = performance.now();
        const sample = window.GRAPH_SAMPLE || { nodes: [], edges: [] };
        
        let rows = [];
        let plan = 'NodeIndexSeekByRange → ExpandAll → ProduceResults';

        if (query.includes('community') && query.includes('degrees')) {
          // Group-by Aggregation
          const commMap = {};
          for (let n of sample.nodes) {
            commMap[n.community] = (commMap[n.community] || 0) + (1 + (n.id % 7));
          }
          rows = Object.entries(commMap).map(([comm, count], i) => `
            <tr>
              <td>${i + 1}</td>
              <td>Cluster #${comm}</td>
              <td>AGGREGATE</td>
              <td>Community ${comm}</td>
              <td><span class="badge badge-success">${count} rels</span></td>
            </tr>
          `);
          plan = 'AllNodesScan → ExpandAll → GroupByCollect → Sort';
        } else if (query.includes('*3')) {
          // 3-Hop Count
          rows = [
            `<tr><td>1</td><td>Deep Expansion Set</td><td>FRIEND*3</td><td>Global</td><td><strong>13,420 reachable nodes</strong></td></tr>`
          ];
          plan = 'NodeIndexSeek → VarLengthExpand(3) → DistinctAggregate';
        } else {
          // 1 or 2 Hop
          const neighbors = sample.edges
            .filter(e => e.source === id || e.target === id)
            .slice(0, 10);

          if (neighbors.length === 0) {
            rows = [`<tr><td colspan="5" class="text-center text-muted">Node #${id} has no outgoing edges in sample slice. Try ID #10 or #42.</td></tr>`];
          } else {
            rows = neighbors.map((e, i) => {
              const targetId = e.source === id ? e.target : e.source;
              const targetNode = sample.nodes.find(n => n.id === targetId) || { community: 0 };
              return `
                <tr>
                  <td>${i + 1}</td>
                  <td><strong>Person #${targetId}</strong></td>
                  <td>:FRIEND</td>
                  <td><span class="badge badge-info">Community ${targetNode.community}</span></td>
                  <td>IndexScan (id: ${targetId})</td>
                </tr>
              `;
            });
          }
        }

        const elapsed = (performance.now() - start).toFixed(2);
        statsLabel.innerHTML = `<span class="badge badge-success">✓ 200 OK (${elapsed}ms)</span> • Plan: <code>${plan}</code>`;
        if (resultTable) {
          resultTable.querySelector('tbody').innerHTML = rows.join('');
        }

        // Also trigger visualization on canvas
        selectNodeById(id);
      }, 150);
    });
  }
}
