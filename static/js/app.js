/* Boekhoudsysteem - JavaScript */

// ============================================================
// Dynamische factuurregels
// ============================================================
let regelTeller = 1;

function voegRegelToe() {
    const container = document.getElementById('factuur-regels');
    if (!container) return;

    const template = document.getElementById('regel-template');
    if (template) {
        const clone = template.content.cloneNode(true);
        const regelDiv = clone.querySelector('.factuur-regel');
        regelDiv.dataset.index = regelTeller;

        // Update name attributes
        clone.querySelectorAll('[name]').forEach(el => {
            el.name = el.name.replace('[]', '[]');
        });

        container.appendChild(clone);
        regelTeller++;
        updateTotalen();
    }
}

function verwijderRegel(btn) {
    const regel = btn.closest('.factuur-regel');
    if (document.querySelectorAll('.factuur-regel').length > 1) {
        regel.remove();
        updateTotalen();
    }
}

function updateTotalen() {
    let subtotaal = 0;
    let btwTotaal = 0;

    document.querySelectorAll('.factuur-regel').forEach(regel => {
        const aantal = parseFloat(regel.querySelector('.regel-aantal')?.value) || 0;
        const prijs = parseFloat(regel.querySelector('.regel-prijs')?.value) || 0;
        const btwPct = parseFloat(regel.querySelector('.regel-btw')?.value) || 0;

        const netto = aantal * prijs;
        const btw = netto * (btwPct / 100);
        const totaal = netto + btw;

        const totaalVeld = regel.querySelector('.regel-totaal');
        if (totaalVeld) {
            totaalVeld.textContent = formatBedrag(totaal);
        }

        subtotaal += netto;
        btwTotaal += btw;
    });

    const subtotaalEl = document.getElementById('subtotaal');
    const btwEl = document.getElementById('btw-totaal');
    const totaalEl = document.getElementById('totaal');

    if (subtotaalEl) subtotaalEl.textContent = formatBedrag(subtotaal);
    if (btwEl) btwEl.textContent = formatBedrag(btwTotaal);
    if (totaalEl) totaalEl.textContent = formatBedrag(subtotaal + btwTotaal);
}

function formatBedrag(bedrag) {
    return '\u20ac ' + bedrag.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Event delegation for dynamic invoice lines
document.addEventListener('input', function(e) {
    if (e.target.matches('.regel-aantal, .regel-prijs, .regel-btw')) {
        updateTotalen();
    }
});

// ============================================================
// Dashboard grafieken
// ============================================================
function laadDashboardGrafieken() {
    laadOmzetGrafiek();
    laadCashflowGrafiek();
}

function laadOmzetGrafiek() {
    const ctx = document.getElementById('omzetGrafiek');
    if (!ctx) return;

    fetch('/api/omzet-per-maand')
        .then(r => r.json())
        .then(data => {
            const maanden = ['Jan', 'Feb', 'Mrt', 'Apr', 'Mei', 'Jun',
                             'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'];
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: maanden,
                    datasets: [
                        {
                            label: 'Omzet',
                            data: data.map(d => d.omzet),
                            backgroundColor: 'rgba(26, 188, 156, 0.7)',
                            borderColor: '#1abc9c',
                            borderWidth: 1
                        },
                        {
                            label: 'Kosten',
                            data: data.map(d => d.kosten),
                            backgroundColor: 'rgba(231, 76, 60, 0.7)',
                            borderColor: '#e74c3c',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: v => '\u20ac ' + v.toLocaleString('nl-NL')
                            }
                        }
                    }
                }
            });
        });
}

function laadCashflowGrafiek() {
    const ctx = document.getElementById('cashflowGrafiek');
    if (!ctx) return;

    fetch('/api/cashflow-per-maand')
        .then(r => r.json())
        .then(data => {
            const maanden = ['Jan', 'Feb', 'Mrt', 'Apr', 'Mei', 'Jun',
                             'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'];
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: maanden,
                    datasets: [
                        {
                            label: 'Inkomend',
                            data: data.map(d => d.inkomend),
                            borderColor: '#27ae60',
                            backgroundColor: 'rgba(39, 174, 96, 0.1)',
                            fill: true,
                            tension: 0.3
                        },
                        {
                            label: 'Uitgaand',
                            data: data.map(d => d.uitgaand),
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            fill: true,
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: v => '\u20ac ' + v.toLocaleString('nl-NL')
                            }
                        }
                    }
                }
            });
        });
}

// Init on page load
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('omzetGrafiek')) {
        laadDashboardGrafieken();
    }
    updateTotalen();
});
