/**
 * Spec Comparer Pro - Frontend JavaScript
 * Handles RFP input, API calls, and enhanced results display
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const rfpText = document.getElementById('rfpText');
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const fileName = document.getElementById('fileName');
    const compareBtn = document.getElementById('compareBtn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const comparisons = document.getElementById('comparisons');
    const oemSummary = document.getElementById('oemSummary');
    const reqCount = document.getElementById('reqCount');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    let selectedFile = null;
    
    // Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${tab}-tab`).classList.add('active');
        });
    });
    
    // Drop Zone Handling
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length && files[0].type === 'application/pdf') {
            selectedFile = files[0];
            fileName.textContent = `📄 ${selectedFile.name}`;
        }
    });
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            selectedFile = fileInput.files[0];
            fileName.textContent = `📄 ${selectedFile.name}`;
        }
    });
    
    // Compare Button Click
    compareBtn.addEventListener('click', async () => {
        const text = rfpText.value.trim();
        const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
        
        if (activeTab === 'text' && !text) {
            alert('Please enter RFP text to compare');
            return;
        }
        
        if (activeTab === 'file' && !selectedFile) {
            alert('Please select a PDF file to upload');
            return;
        }
        
        // Show loading
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        comparisons.innerHTML = '';
        oemSummary.innerHTML = '';
        
        try {
            const formData = new FormData();
            
            if (activeTab === 'text') {
                formData.append('rfp_text', text);
            } else {
                formData.append('file', selectedFile);
            }
            
            // Add analysis options
            formData.append('include_calculations', document.getElementById('includeCalculations').checked);
            formData.append('include_recommendations', document.getElementById('includeRecommendations').checked);
            formData.append('include_budget', document.getElementById('includeBudgetAnalysis').checked);
            formData.append('include_oem_comparison', document.getElementById('includeOemComparison').checked);
            formData.append('cable_length', document.getElementById('cableLength').value);
            formData.append('application', document.getElementById('applicationSelect').value);
            
            const response = await fetch('/api/compare', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Comparison failed');
            }
            
            displayResults(data);
            
        } catch (error) {
            console.error('Comparison error:', error);
            alert(`Error: ${error.message}`);
        } finally {
            loading.classList.add('hidden');
        }
    });
    
    /**
     * Display comparison results with enhanced data
     */
    function displayResults(data) {
        if (!data.comparisons || data.comparisons.length === 0) {
            comparisons.innerHTML = `
                <div class="no-matches">
                    <p>⚠️ No wire/cable specifications found in the RFP text.</p>
                    <p style="margin-top: 8px; font-size: 0.9rem;">
                        Try including specifications like "2.5 sq mm 3 core copper wire"
                    </p>
                </div>
            `;
            results.classList.remove('hidden');
            reqCount.textContent = '0 requirements found';
            return;
        }
        
        const appNames = {
            'residential': '🏠 Residential', 'commercial': '🏢 Commercial',
            'industrial': '🏭 Industrial', 'hospital': '🏥 Hospital',
            'data_center': '💻 Data Center', 'high_rise': '🏗️ High Rise',
            'underground': '⬇️ Underground', 'outdoor': '☀️ Outdoor'
        };
        
        reqCount.innerHTML = `${data.comparisons.length} requirement${data.comparisons.length > 1 ? 's' : ''} found 
            ${data.detected_application ? `| Detected: <strong>${appNames[data.detected_application] || data.detected_application}</strong>` : ''}
            ${data.analysis_options?.cable_length ? `| Cable Length: <strong>${data.analysis_options.cable_length}m</strong>` : ''}`;
        
        // Display OEM Summary
        if (data.oem_summary && data.oem_summary.oem_rankings) {
            oemSummary.innerHTML = `
                <div class="oem-summary-card">
                    <h3>🏆 OEM Performance Summary</h3>
                    <div class="oem-ranking-grid">
                        ${data.oem_summary.oem_rankings.map((oem, idx) => `
                            <div class="oem-rank-card ${idx === 0 ? 'best' : ''}">
                                <div class="oem-rank-badge">${idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '#' + (idx + 1)}</div>
                                <div class="oem-rank-name">${oem.oem}</div>
                                <div class="oem-rank-stats">
                                    <span>Appearances: <strong>${oem.appearances}</strong></span>
                                    <span>Avg Match: <strong>${oem.avg_match_score}%</strong></span>
                                    ${oem.avg_price ? `<span>Avg Price: <strong>₹${oem.avg_price}/m</strong></span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Build comparison cards
        let html = '';
        
        data.comparisons.forEach((comp, idx) => {
            const req = comp.requirement;
            const matches = comp.top_matches;
            
            html += `
                <div class="comparison-card">
                    <div class="requirement-header">
                        <h3>📋 Requirement #${idx + 1}</h3>
                        ${req.original_text ? `<p style="margin-bottom: 8px; color: var(--text-secondary);">"${req.original_text}"</p>` : ''}
                        <div class="requirement-specs">
                            ${req.conductor_size ? `<span class="spec-tag"><strong>${req.conductor_size}</strong> sq mm</span>` : ''}
                            ${req.cores ? `<span class="spec-tag"><strong>${req.cores}</strong> Core</span>` : ''}
                            ${req.voltage ? `<span class="spec-tag"><strong>${req.voltage}</strong>V</span>` : ''}
                            ${req.conductor_material ? `<span class="spec-tag"><strong>${req.conductor_material}</strong></span>` : ''}
                            ${req.insulation ? `<span class="spec-tag"><strong>${req.insulation}</strong></span>` : ''}
                            ${req.armoured !== undefined ? `<span class="spec-tag">${req.armoured ? '🛡️ Armoured' : 'Unarmoured'}</span>` : ''}
                            ${req.current_rating ? `<span class="spec-tag"><strong>${req.current_rating}</strong> Amp</span>` : ''}
                        </div>
                    </div>
                    
                    <div class="matches-container">
                        ${matches.length === 0 ? 
                            '<div class="no-matches">❌ No matching products found</div>' :
                            `<div class="match-grid">${matches.map((m, i) => createEnhancedMatchCard(m, i + 1, req)).join('')}</div>
                             ${createComparisonTable(matches, req, idx)}`
                        }
                    </div>
                </div>
            `;
        });
        
        comparisons.innerHTML = html;
        results.classList.remove('hidden');
        
        // Add toggle event listeners
        document.querySelectorAll('.toggle-table-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const table = btn.nextElementSibling;
                table.classList.toggle('visible');
                btn.textContent = table.classList.contains('visible') 
                    ? '📊 Hide Comparison Table' 
                    : '📊 Show Comparison Table';
            });
        });
        
        document.querySelectorAll('.toggle-calc-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const panel = btn.nextElementSibling;
                panel.classList.toggle('visible');
                btn.textContent = panel.classList.contains('visible') 
                    ? '📉 Hide Calculations' 
                    : '📊 Show Calculations';
            });
        });
    }
    
    /**
     * Create enhanced match card with calculations and recommendations
     */
    function createEnhancedMatchCard(match, rank, requirement) {
        const scoreClass = match.match_score >= 70 ? 'high' : 
                          match.match_score >= 50 ? 'medium' : 'low';
        
        // Build calculations panel
        let calculationsHtml = '';
        if (match.voltage_drop || match.power_capacity || match.short_circuit) {
            const vd = match.voltage_drop || {};
            const pc = match.power_capacity || {};
            const sc = match.short_circuit || {};
            
            const vdStatusClass = vd.status === 'Excellent' ? 'excellent' : 
                                  vd.status === 'Good' ? 'good' : 
                                  vd.status === 'Acceptable' ? 'acceptable' : 'warning';
            
            calculationsHtml = `
                <div class="calculations-section">
                    <button class="toggle-calc-btn">📊 Show Calculations</button>
                    <div class="calculations-panel">
                        ${vd.drop_percent !== undefined ? `
                        <div class="calc-item">
                            <div class="calc-label">⚡ Voltage Drop (${vd.cable_length}m)</div>
                            <div class="calc-value ${vdStatusClass}">${vd.drop_percent?.toFixed(2)}%</div>
                            <div class="calc-status">${vd.status} | ${vd.drop_volts?.toFixed(2)}V drop</div>
                            <div class="calc-compliance">
                                Feeder: ${vd.compliant_feeder ? '✅' : '❌'} | Branch: ${vd.compliant_branch ? '✅' : '❌'}
                            </div>
                        </div>` : ''}
                        
                        ${pc.power_kw !== undefined ? `
                        <div class="calc-item">
                            <div class="calc-label">⚡ Power Capacity</div>
                            <div class="calc-value">${pc.power_kw?.toFixed(1)} kW / ${pc.power_kva?.toFixed(1)} kVA</div>
                            <div class="calc-status">Derated Current: ${pc.current_capacity?.toFixed(1)} A</div>
                        </div>` : ''}
                        
                        ${sc.withstand_1s_kA !== undefined ? `
                        <div class="calc-item">
                            <div class="calc-label">⚡ Short Circuit Withstand</div>
                            <div class="calc-value">${sc.withstand_1s_kA?.toFixed(2)} kA</div>
                            <div class="calc-status">I²t: ${sc.i2t_rating ? (sc.i2t_rating / 1000000).toFixed(2) + 'M' : '-'} A²s</div>
                        </div>` : ''}
                    </div>
                </div>
            `;
        }
        
        // Build recommendations
        let recommendationsHtml = '';
        if (match.recommendations && match.recommendations.length > 0) {
            recommendationsHtml = `
                <div class="recommendations-section">
                    <div class="recommendations-label">💡 Recommendations</div>
                    <ul class="recommendations-list">
                        ${match.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Build budget analysis
        let budgetHtml = '';
        if (match.budget_analysis) {
            const ba = match.budget_analysis;
            budgetHtml = `
                <div class="budget-section">
                    <div class="budget-total">
                        <span class="budget-label">Total Cost (${ba.cable_length}m)</span>
                        <span class="budget-value">₹${ba.total_cost?.toLocaleString()}</span>
                    </div>
                    <div class="budget-rating">${ba.value_rating}</div>
                </div>
            `;
        }
        
        return `
            <div class="match-card rank-${rank}">
                <div class="match-rank">#${rank}</div>
                <div class="match-oem">${match.oem || 'Unknown'}</div>
                <div class="match-name">${match.product_name || 'N/A'}</div>
                <div class="match-code">${match.product_code || ''}</div>
                
                <div class="match-score ${scoreClass}">
                    ${match.match_score}% Match
                </div>
                
                <div class="match-specs">
                    <div class="match-spec">
                        <span class="match-spec-label">Size</span>
                        <span class="match-spec-value">${match.conductor_size || '-'} sq mm</span>
                    </div>
                    <div class="match-spec">
                        <span class="match-spec-label">Cores</span>
                        <span class="match-spec-value">${match.cores || '-'}</span>
                    </div>
                    <div class="match-spec">
                        <span class="match-spec-label">Voltage</span>
                        <span class="match-spec-value">${match.voltage_rating || '-'}</span>
                    </div>
                    <div class="match-spec">
                        <span class="match-spec-label">Material</span>
                        <span class="match-spec-value">${match.conductor_material || '-'}</span>
                    </div>
                    <div class="match-spec">
                        <span class="match-spec-label">Insulation</span>
                        <span class="match-spec-value">${match.insulation_type || '-'}</span>
                    </div>
                    <div class="match-spec">
                        <span class="match-spec-label">Current</span>
                        <span class="match-spec-value">${match.current_rating || '-'} A</span>
                    </div>
                </div>
                
                ${match.price_per_meter && !match.budget_analysis ? `
                    <div class="match-price">
                        ₹${parseFloat(match.price_per_meter).toFixed(2)}/m
                    </div>
                ` : ''}
                
                ${budgetHtml}
                ${recommendationsHtml}
                ${calculationsHtml}
            </div>
        `;
    }
    
    /**
     * Create comparison table for all top matches
     */
    function createComparisonTable(matches, requirement, idx) {
        if (matches.length === 0) return '';
        
        const specs = [
            { key: 'conductor_size', label: 'Conductor Size', reqKey: 'conductor_size', unit: 'sq mm' },
            { key: 'cores', label: 'No. of Cores', reqKey: 'cores', unit: '' },
            { key: 'voltage_rating', label: 'Voltage Rating', reqKey: 'voltage', unit: '' },
            { key: 'conductor_material', label: 'Conductor Material', reqKey: 'conductor_material', unit: '' },
            { key: 'insulation_type', label: 'Insulation Type', reqKey: 'insulation', unit: '' },
            { key: 'current_rating', label: 'Current Rating', reqKey: 'current_rating', unit: 'A' },
            { key: 'standard', label: 'Standard', reqKey: 'standard', unit: '' },
            { key: 'is_armoured', label: 'Armoured', reqKey: 'armoured', unit: '' },
            { key: 'price_per_meter', label: 'Price/Meter', reqKey: null, unit: '₹' },
            { key: 'overall_quality_score', label: 'Quality Score', reqKey: null, unit: '/100' },
        ];
        
        let tableHtml = `
            <div class="comparison-table-wrapper">
                <button class="toggle-table-btn">📊 Show Comparison Table</button>
                <table class="comparison-table" id="table-${idx}">
                    <thead>
                        <tr>
                            <th>Specification</th>
                            <th>RFP Required</th>
                            ${matches.map((m, i) => `<th>#${i+1} ${m.oem}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        specs.forEach(spec => {
            const reqValue = requirement[spec.reqKey];
            const reqDisplay = formatValue(reqValue, spec.unit, spec.key);
            
            tableHtml += `
                <tr>
                    <td><strong>${spec.label}</strong></td>
                    <td>${reqDisplay || '-'}</td>
                    ${matches.map(m => {
                        const val = m[spec.key];
                        const display = formatValue(val, spec.unit, spec.key);
                        const matchClass = getMatchClass(val, reqValue, spec.key);
                        return `<td class="${matchClass}">${display || '-'}</td>`;
                    }).join('')}
                </tr>
            `;
        });
        
        tableHtml += `
                    </tbody>
                </table>
            </div>
        `;
        
        return tableHtml;
    }
    
    /**
     * Format value for display
     */
    function formatValue(value, unit, key) {
        if (value === null || value === undefined || value === '') return null;
        
        if (key === 'is_armoured' || key === 'armoured') {
            if (typeof value === 'boolean') return value ? 'Yes' : 'No';
            return parseInt(value) ? 'Yes' : 'No';
        }
        
        if (key === 'price_per_meter' && value) {
            return `₹${parseFloat(value).toFixed(2)}`;
        }
        
        if (unit) {
            return `${value}${unit}`;
        }
        
        return value;
    }
    
    /**
     * Determine match class for table cell styling
     */
    function getMatchClass(productVal, reqVal, key) {
        if (reqVal === null || reqVal === undefined) return '';
        if (productVal === null || productVal === undefined) return 'mismatch';
        
        const pVal = String(productVal).toLowerCase();
        const rVal = String(reqVal).toLowerCase();
        
        if (key === 'conductor_size' || key === 'cores' || key === 'current_rating') {
            const pNum = parseFloat(productVal);
            const rNum = parseFloat(reqVal);
            if (isNaN(pNum) || isNaN(rNum)) return 'mismatch';
            
            if (pNum === rNum) return 'match';
            if (Math.abs(pNum - rNum) / rNum < 0.1) return 'partial';
            if (key === 'current_rating' && pNum >= rNum) return 'match';
            return 'mismatch';
        }
        
        if (key === 'is_armoured' || key === 'armoured') {
            const pBool = pVal === 'yes' || pVal === '1' || pVal === 'true';
            const rBool = typeof reqVal === 'boolean' ? reqVal : rVal === 'yes' || rVal === '1' || rVal === 'true';
            return pBool === rBool ? 'match' : 'mismatch';
        }
        
        if (pVal === rVal) return 'match';
        if (pVal.includes(rVal) || rVal.includes(pVal)) return 'partial';
        return 'mismatch';
    }
});
