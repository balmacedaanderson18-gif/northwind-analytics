/**
 * Northwind Business Intelligence Dashboard Engine
 * Interacción completa con API Backend, renderizado de gráficos Chart.js y tablas dinámicas.
 */

// Instancias de Gráficos globales para actualización limpia
let charts = {};

// Paleta de colores curada
const PALETTE = {
  primary: '#6366f1',
  cyan: '#06b6d4',
  emerald: '#10b981',
  amber: '#f59e0b',
  rose: '#f43f5e',
  purple: '#a855f7',
  blue: '#3b82f6',
  slate: '#64748b',
  chartColors: [
    '#6366f1', '#06b6d4', '#10b981', '#f59e0b', 
    '#a855f7', '#f43f5e', '#3b82f6', '#ec4899', '#84cc16'
  ]
};

// Formateador de moneda USD
const formatCurrency = (val) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(val || 0);
};

// Formateador de enteros
const formatNumber = (val) => {
  return new Intl.NumberFormat('en-US').format(val || 0);
};

// Inicialización de la Aplicación
document.addEventListener('DOMContentLoaded', async () => {
  await loadFilterOptions();
  await refreshDashboard();
});

// Navegación entre Pestañas / Vistas
function switchTab(viewId) {
  // Actualizar botones de navegación
  document.querySelectorAll('.nav-item button').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`nav-${viewId}`);
  if (activeBtn) activeBtn.classList.add('active');

  // Actualizar secciones de contenido
  document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
  const activeSection = document.getElementById(`view-${viewId}`);
  if (activeSection) activeSection.classList.add('active');

  // Actualizar títulos
  const titles = {
    overview: { title: 'Tablero Principal de Ventas', sub: 'Análisis financiero y métricas netas de rendimiento empresarial' },
    categories: { title: 'Rendimiento de Categorías & Catálogo', sub: 'Desglose de ingresos netos por categoría y top productos' },
    rfm: { title: 'Segmentación de Clientes (RFM & Clustering)', sub: 'Análisis de Recencia, Frecuencia, Valor Monetario y Clustering K-Means' },
    employees: { title: 'Fuerza de Ventas & Estructura Organizacional', sub: 'Ventas netas por representante y jerarquía de supervisión' },
    logistics: { title: 'Logística, Transportistas y Envíos', sub: 'Evaluación de eficiencia operativa, puntualidad y fletes cobrados' },
    reconciliation: { title: 'Auditoría & Reconciliación de Totales', sub: 'Conciliación matemática estricta de las cifras de la base de datos vs archivo Excel' }
  };

  if (titles[viewId]) {
    document.getElementById('view-title').textContent = titles[viewId].title;
    document.getElementById('view-subtitle').textContent = titles[viewId].sub;
  }

  // Cargar datos específicos si se requiere
  if (viewId === 'categories') loadCategoriesData();
  if (viewId === 'rfm') loadRFMData();
  if (viewId === 'employees') loadEmployeesData();
  if (viewId === 'logistics') loadLogisticsData();
}

// Cargar opciones para los filtros globales
async function loadFilterOptions() {
  try {
    const res = await fetch('/api/metadata/filters');
    const data = await res.json();

    const catSelect = document.getElementById('filter-category');
    data.categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat.categoryid;
      opt.textContent = cat.categoryname;
      catSelect.appendChild(opt);
    });

    const countrySelect = document.getElementById('filter-country');
    data.countries.forEach(ctry => {
      const opt = document.createElement('option');
      opt.value = ctry;
      opt.textContent = ctry;
      countrySelect.appendChild(opt);
    });
  } catch (err) {
    console.error('Error al cargar filtros:', err);
  }
}

// Aplicar filtros dinámicos
async function applyFilters() {
  await refreshDashboard();
  const currentView = document.querySelector('.view-section.active').id.replace('view-', '');
  if (currentView === 'categories') loadCategoriesData();
}

function resetFilters() {
  document.getElementById('filter-category').value = '';
  document.getElementById('filter-country').value = '';
  applyFilters();
}

// Obtener parámetros de filtro
function getFilterParams() {
  const params = new URLSearchParams();
  const cat = document.getElementById('filter-category').value;
  const ctry = document.getElementById('filter-country').value;
  if (cat) params.append('category_id', cat);
  if (ctry) params.append('country', ctry);
  return params.toString();
}

// Refrescar KPIs y Gráficos Principales
async function refreshDashboard() {
  const query = getFilterParams();

  try {
    // 1. Cargar KPIs
    const kpiRes = await fetch(`/api/kpis?${query}`);
    const kpi = await kpiRes.json();

    document.getElementById('kpi-net-sales').textContent = formatCurrency(kpi.net_sales);
    document.getElementById('kpi-orders').textContent = formatNumber(kpi.total_orders);
    document.getElementById('kpi-aov').textContent = formatCurrency(kpi.average_order_value);
    document.getElementById('kpi-discounts').textContent = formatCurrency(kpi.total_discount);
    document.getElementById('kpi-freight').textContent = formatCurrency(kpi.total_freight);

    // 2. Cargar Tendencia de Ventas
    const trendRes = await fetch(`/api/sales-trend?${query}`);
    const trendData = await trendRes.json();

    renderSalesTrendChart(trendData);
    renderGrossVsNetChart(kpi);
  } catch (err) {
    console.error('Error actualizando dashboard:', err);
  }
}

// Renderizar Gráfico de Tendencia Mensual
function renderSalesTrendChart(data) {
  const ctx = document.getElementById('chart-sales-trend').getContext('2d');
  if (charts['salesTrend']) charts['salesTrend'].destroy();

  const labels = data.map(d => d.period);
  const netSales = data.map(d => d.net_sales);
  const discounts = data.map(d => d.discount_amount);

  charts['salesTrend'] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Ventas Netas ($)',
          data: netSales,
          borderColor: PALETTE.primary,
          backgroundColor: 'rgba(99, 102, 241, 0.15)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 3
        },
        {
          label: 'Descuentos Otorgados ($)',
          data: discounts,
          borderColor: PALETTE.amber,
          backgroundColor: 'rgba(245, 158, 11, 0.08)',
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 2,
          borderDash: [4, 4]
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#9ca3af', font: { family: 'Inter' } } }
      },
      scales: {
        x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
        y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
      }
    }
  });
}

// Renderizar Gráfico Doughnut: Brutas vs Descuentos
function renderGrossVsNetChart(kpi) {
  const ctx = document.getElementById('chart-gross-net').getContext('2d');
  if (charts['grossNet']) charts['grossNet'].destroy();

  charts['grossNet'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Ventas Netas', 'Descuentos'],
      datasets: [{
        data: [kpi.net_sales, kpi.total_discount],
        backgroundColor: [PALETTE.primary, PALETTE.amber],
        borderColor: '#111827',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Inter' } } }
      },
      cutout: '70%'
    }
  });
}

// ----------------------------------------------------------------------------
// SECCIÓN: CATEGORÍAS & PRODUCTOS
// ----------------------------------------------------------------------------
async function loadCategoriesData() {
  try {
    const [catRes, prodRes] = await Promise.all([
      fetch('/api/categories-analysis'),
      fetch('/api/top-products?limit=15')
    ]);

    const categories = await catRes.json();
    const products = await prodRes.json();

    // Gráfico de Participación de Categorías (Pie)
    const ctxShare = document.getElementById('chart-categories-share').getContext('2d');
    if (charts['catShare']) charts['catShare'].destroy();

    charts['catShare'] = new Chart(ctxShare, {
      type: 'pie',
      data: {
        labels: categories.map(c => c.categoryname),
        datasets: [{
          data: categories.map(c => c.net_sales),
          backgroundColor: PALETTE.chartColors,
          borderWidth: 2,
          borderColor: '#111827'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { color: '#9ca3af', font: { family: 'Inter', size: 11 } } }
        }
      }
    });

    // Gráfico de Unidades por Categoría (Bar)
    const ctxUnits = document.getElementById('chart-categories-units').getContext('2d');
    if (charts['catUnits']) charts['catUnits'].destroy();

    charts['catUnits'] = new Chart(ctxUnits, {
      type: 'bar',
      data: {
        labels: categories.map(c => c.categoryname),
        datasets: [{
          label: 'Unidades Vendidas',
          data: categories.map(c => c.units_sold),
          backgroundColor: PALETTE.cyan,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
        }
      }
    });

    // Tabla de Top Productos
    const tbody = document.querySelector('#table-top-products tbody');
    tbody.innerHTML = '';
    products.forEach(p => {
      const statusBadge = p.discontinued === 1 
        ? `<span class="badge-tag tag-lost">Discontinuado</span>` 
        : `<span class="badge-tag tag-champions">Activo</span>`;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${p.productid}</strong></td>
        <td>${p.productname}</td>
        <td>${p.categoryname}</td>
        <td>${p.supplier}</td>
        <td>${formatCurrency(p.catalog_price)}</td>
        <td>${formatNumber(p.units_sold)}</td>
        <td><strong>${formatCurrency(p.net_sales)}</strong></td>
        <td>${p.stock}</td>
        <td>${p.on_order}</td>
        <td>${statusBadge}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Error cargando categorías:', err);
  }
}

// ----------------------------------------------------------------------------
// SECCIÓN: CLIENTES (RFM & CLUSTERING)
// ----------------------------------------------------------------------------
async function loadRFMData() {
  try {
    const res = await fetch('/api/customers-rfm');
    const data = await res.json();

    // Gráfico de Distribución por Segmento (Bar horizontal)
    const ctxDist = document.getElementById('chart-rfm-distribution').getContext('2d');
    if (charts['rfmDist']) charts['rfmDist'].destroy();

    charts['rfmDist'] = new Chart(ctxDist, {
      type: 'bar',
      data: {
        labels: data.rfm_summary.map(s => s.rfm_segment),
        datasets: [{
          label: 'Cantidad de Clientes',
          data: data.rfm_summary.map(s => s.count),
          backgroundColor: PALETTE.purple,
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
        }
      }
    });

    // Gráfico de Valor Monetario por Segmento (Doughnut)
    const ctxMon = document.getElementById('chart-rfm-monetary').getContext('2d');
    if (charts['rfmMon']) charts['rfmMon'].destroy();

    charts['rfmMon'] = new Chart(ctxMon, {
      type: 'doughnut',
      data: {
        labels: data.rfm_summary.map(s => s.rfm_segment),
        datasets: [{
          data: data.rfm_summary.map(s => s.total_monetary),
          backgroundColor: PALETTE.chartColors,
          borderWidth: 2,
          borderColor: '#111827'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { color: '#9ca3af', font: { family: 'Inter', size: 10 } } }
        }
      }
    });

    // Tabla de Clientes con Segmentación
    const tbody = document.querySelector('#table-rfm-customers tbody');
    tbody.innerHTML = '';
    
    const tagClassMap = {
      'Campeones (Champions)': 'tag-champions',
      'Clientes Leales (Loyal)': 'tag-loyal',
      'Prometedores Recientes (Promising)': 'tag-promising',
      'En Riesgo / Alto Valor (At Risk)': 'tag-risk',
      'Dormidos / Perdidos (Lost)': 'tag-lost',
      'Necesitan Atención (Need Attention)': 'tag-attention',
      'Prospectos Sin Órdenes (Lead)': 'tag-lost'
    };

    data.customers.forEach(c => {
      const tagClass = tagClassMap[c.rfm_segment] || 'tag-attention';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${c.customerid}</strong></td>
        <td>${c.companyname}</td>
        <td>${c.country}</td>
        <td>${c.recency}</td>
        <td>${c.frequency}</td>
        <td><strong>${formatCurrency(c.monetary)}</strong></td>
        <td><span class="badge-tag ${tagClass}">${c.rfm_segment}</span></td>
        <td><span style="font-size:0.75rem; color:#c7d2fe;">${c.cluster_name}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Error cargando RFM:', err);
  }
}

// ----------------------------------------------------------------------------
// SECCIÓN: EMPLEADOS & FUERZA DE VENTAS
// ----------------------------------------------------------------------------
async function loadEmployeesData() {
  try {
    const res = await fetch('/api/employees-performance');
    const employees = await res.json();

    // Gráfico de Ventas por Empleado
    const ctxSales = document.getElementById('chart-employees-sales').getContext('2d');
    if (charts['empSales']) charts['empSales'].destroy();

    charts['empSales'] = new Chart(ctxSales, {
      type: 'bar',
      data: {
        labels: employees.map(e => e.employee_name),
        datasets: [{
          label: 'Ventas Netas ($)',
          data: employees.map(e => e.net_sales),
          backgroundColor: PALETTE.emerald,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
        }
      }
    });

    // Gráfico de Pedidos Gestionados
    const ctxOrders = document.getElementById('chart-employees-orders').getContext('2d');
    if (charts['empOrders']) charts['empOrders'].destroy();

    charts['empOrders'] = new Chart(ctxOrders, {
      type: 'bar',
      data: {
        labels: employees.map(e => e.employee_name),
        datasets: [{
          label: 'Total Pedidos',
          data: employees.map(e => e.total_orders),
          backgroundColor: PALETTE.cyan,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
        }
      }
    });

    // Tabla de Empleados
    const tbody = document.querySelector('#table-employees tbody');
    tbody.innerHTML = '';
    employees.forEach(e => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${e.employeeid}</strong></td>
        <td><strong>${e.employee_name}</strong></td>
        <td>${e.title}</td>
        <td>${e.city}, ${e.country}</td>
        <td><span style="color:#a5b4fc;">${e.manager_name}</span></td>
        <td>${e.total_orders}</td>
        <td>${formatNumber(e.total_units)}</td>
        <td><strong>${formatCurrency(e.net_sales)}</strong></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Error cargando empleados:', err);
  }
}

// ----------------------------------------------------------------------------
// SECCIÓN: LOGÍSTICA & FLETES
// ----------------------------------------------------------------------------
async function loadLogisticsData() {
  try {
    const res = await fetch('/api/logistics');
    const data = await res.json();

    // Gráfico Cuota de Shippers (Doughnut)
    const ctxShare = document.getElementById('chart-shippers-share').getContext('2d');
    if (charts['shipShare']) charts['shipShare'].destroy();

    charts['shipShare'] = new Chart(ctxShare, {
      type: 'doughnut',
      data: {
        labels: data.shippers.map(s => s.shipper_name),
        datasets: [{
          data: data.shippers.map(s => s.total_shipments),
          backgroundColor: [PALETTE.primary, PALETTE.cyan, PALETTE.amber, PALETTE.emerald],
          borderWidth: 2,
          borderColor: '#111827'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Inter' } } }
        }
      }
    });

    // Gráfico Puntualidad en Envíos (Bar)
    const ctxOntime = document.getElementById('chart-shippers-ontime').getContext('2d');
    if (charts['shipOntime']) charts['shipOntime'].destroy();

    charts['shipOntime'] = new Chart(ctxOntime, {
      type: 'bar',
      data: {
        labels: data.shippers.map(s => s.shipper_name),
        datasets: [{
          label: 'Puntualidad (%)',
          data: data.shippers.map(s => s.on_time_rate_pct),
          backgroundColor: PALETTE.emerald,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 80, max: 100, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
        }
      }
    });

    // Tabla de Shippers
    const tbody = document.querySelector('#table-shippers tbody');
    tbody.innerHTML = '';
    data.shippers.forEach(s => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${s.shipperid}</strong></td>
        <td><strong>${s.shipper_name}</strong></td>
        <td>${s.phone}</td>
        <td>${s.total_shipments}</td>
        <td>${formatCurrency(s.total_freight)}</td>
        <td>${formatCurrency(s.avg_freight_per_order)}</td>
        <td>${s.avg_lead_days} días</td>
        <td><span style="color:#fb7185;">${s.delayed_orders}</span></td>
        <td><strong style="color:#34d399;">${s.on_time_rate_pct}%</strong></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Error cargando logística:', err);
  }
}
