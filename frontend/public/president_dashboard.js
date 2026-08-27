document.addEventListener('DOMContentLoaded', () => {
  // === Tab Switching Logic ===
  const navItems = document.querySelectorAll('.nav-item');
  const tabContents = document.querySelectorAll('.tab-content');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      
      // Remove active from all tabs
      navItems.forEach(nav => nav.classList.remove('active'));
      tabContents.forEach(tab => tab.classList.remove('active'));
      
      // Add active to clicked
      item.classList.add('active');
      const targetId = item.getAttribute('data-target');
      document.getElementById(targetId).classList.add('active');
    });
  });

  // === Chart.js Global Settings ===
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = 'Inter, sans-serif';
  const gridOptions = {
    color: 'rgba(255, 255, 255, 0.05)',
    drawBorder: false
  };

  // === 1. Logistics Chart (Infrastructure Tab) ===
  const ctxLogistics = document.getElementById('logisticsChart').getContext('2d');
  new Chart(ctxLogistics, {
    type: 'bar',
    data: {
      labels: ['Sea Freight', 'Rail', 'Air'],
      datasets: [{
        label: 'Avg Cost per Unit ($)',
        data: [2, 12, 30],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)'
        ],
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: gridOptions, beginAtZero: true },
        x: { grid: { display: false } }
      }
    }
  });

  // === 2. Infrastructure Budget Doughnut ===
  const ctxInfra = document.getElementById('infraBudgetChart').getContext('2d');
  const infraChart = new Chart(ctxInfra, {
    type: 'doughnut',
    data: {
      labels: ['Railroads', 'Ports/Maritime', 'Airports'],
      datasets: [{
        data: [450, 200, 150],
        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b'],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#f8fafc' } }
      },
      cutout: '70%'
    }
  });

  // Dynamic update of doughnut chart based on sliders
  document.getElementById('rail-budget').addEventListener('input', (e) => {
    infraChart.data.datasets[0].data[0] = parseInt(e.target.value);
    infraChart.update();
  });
  document.getElementById('port-budget').addEventListener('input', (e) => {
    infraChart.data.datasets[0].data[1] = parseInt(e.target.value);
    infraChart.update();
  });

  // === 3. Military Radar Chart (Intel Tab) ===
  const ctxRadar = document.getElementById('radarChart').getContext('2d');
  new Chart(ctxRadar, {
    type: 'radar',
    data: {
      labels: ['Army Size', 'Naval Power', 'Air Superiority', 'Intel Network', 'Defense Infra', 'Cyber'],
      datasets: [
        {
          label: 'Valdoria (Us)',
          data: [8, 6, 7, 5, 8, 4],
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          borderColor: '#3b82f6',
          pointBackgroundColor: '#3b82f6',
          borderWidth: 2
        },
        {
          label: 'Drakmoor (AI)',
          data: [9, 8, 5, 7, 6, 8],
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          borderColor: '#ef4444',
          pointBackgroundColor: '#ef4444',
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
          pointLabels: { color: '#94a3b8', font: { size: 11 } },
          ticks: { display: false, min: 0, max: 10 }
        }
      },
      plugins: {
        legend: { labels: { color: '#f8fafc' } }
      }
    }
  });

  // === 4. Macroeconomic Line Chart (Indexes Tab) ===
  const ctxMacro = document.getElementById('macroChart').getContext('2d');
  // Gradient setup for line chart
  const gradient = ctxMacro.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, 'rgba(16, 185, 129, 0.5)');
  gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

  new Chart(ctxMacro, {
    type: 'line',
    data: {
      labels: ['Round 1', 'Round 2', 'Round 3 (Current)'],
      datasets: [{
        label: 'GDP ($ Trillions)',
        data: [1.10, 1.18, 1.24],
        borderColor: '#10b981',
        backgroundColor: gradient,
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleColor: '#fff',
          bodyColor: '#10b981',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1
        }
      },
      scales: {
        y: { grid: gridOptions, min: 1.0 },
        x: { grid: { display: false } }
      }
    }
  });

  // === 5. Debt Profile Stacked Bar (Financing Tab) ===
  const ctxDebt = document.getElementById('debtChart').getContext('2d');
  new Chart(ctxDebt, {
    type: 'bar',
    data: {
      labels: ['R1', 'R2', 'R3', 'R4 (Proj)', 'R5 (Proj)'],
      datasets: [
        {
          label: 'FMI Loans',
          data: [200, 350, 450, 400, 300],
          backgroundColor: '#ef4444',
          stack: 'Stack 0',
        },
        {
          label: 'National Treasury',
          data: [800, 750, 600, 650, 800],
          backgroundColor: '#3b82f6',
          stack: 'Stack 0',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#f8fafc' } }
      },
      scales: {
        y: { 
          stacked: true, 
          grid: gridOptions,
          title: { display: true, text: 'Millions ($)', color: '#94a3b8' }
        },
        x: { 
          stacked: true,
          grid: { display: false }
        }
      }
    }
  });

  // === Budget Calculation ===
  const totalBudget = 2000; // $2,000M starting budget
  const budgetDisplay = document.getElementById('global-budget-display');

  function updateGlobalBudget() {
    const sliders = document.querySelectorAll('.budget-slider');
    let spent = 0;
    sliders.forEach(slider => {
      spent += parseInt(slider.value) || 0;
    });
    
    const remaining = totalBudget - spent;
    
    if (budgetDisplay) {
      budgetDisplay.innerText = '$' + remaining.toLocaleString() + 'M';
      
      if (remaining < 0) {
        budgetDisplay.classList.remove('text-green');
        budgetDisplay.classList.add('text-red');
      } else {
        budgetDisplay.classList.remove('text-red');
        budgetDisplay.classList.add('text-green');
      }
    }
  }

  document.addEventListener('input', (e) => {
    if (e.target.classList.contains('budget-slider')) {
      updateGlobalBudget();
    }
  });

  updateGlobalBudget(); // Initialize

  // === Modal Logic ===
  const mapModal = document.getElementById('map-modal');
  const openMapBtn = document.getElementById('open-map-modal');
  const closeMapBtn = document.getElementById('close-map-modal');

  openMapBtn.addEventListener('click', () => {
    mapModal.classList.add('active');
  });

  closeMapBtn.addEventListener('click', () => {
    mapModal.classList.remove('active');
  });

  // Close modal when clicking outside
  mapModal.addEventListener('click', (e) => {
    if (e.target === mapModal) {
      mapModal.classList.remove('active');
    }
  });
});
