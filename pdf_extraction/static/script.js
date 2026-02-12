// PDF Extractor Frontend JavaScript (Optimized v2.2)
// Supports 100k RFP Terms with Lazy Loading, Chunked Processing & UI Responsiveness

// Configuration - Optimized for 100k database
const CONFIG = {
    API_BASE: '/api',
    MAX_FILE_SIZE: 50 * 1024 * 1024,  // 50MB
    CACHE_TTL: 3600000,  // 1 hour
    PAGINATION_LIMIT: 20,
    CHUNK_SIZE: 10000,  // Process in 10k character chunks
    DEBOUNCE_DELAY: 300,
    REQUEST_TIMEOUT: 120000  // 2 minutes for large files
};

// Performance tracking
const PERF_METRICS = {
    requestStart: 0,
    extractionStart: 0,
    chunks_processed: 0,
    total_chunks: 0
};

// State tracking
let processingAborted = false;
let abortController = null;

// DOM Elements (Cache references for performance)
let pdfFile, extractBtn, downloadFullBtn, downloadReportBtn;
let fileName, errorMessage, loadingIndicator, resultsSection, resultsContainer;
let termsCategories = null;  // Added for renderTermsCategories function
let selectedFile = null;
let isProcessing = false;
let lastExtractedFilename = null;
let debounceTimer = null;
let requestAbortController = null;

// Cache and database stats
let termsCache = null;
let termsCacheTime = 0;
let databaseStats = null;
const TERMS_CACHE_TTL = 60000; // 1 minute

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Get DOM elements
        pdfFile = document.getElementById('pdfFile');
        extractBtn = document.getElementById('extractBtn');
        downloadFullBtn = document.getElementById('downloadFullBtn');
        downloadReportBtn = document.getElementById('downloadReportBtn');
        fileName = document.getElementById('fileName');
        errorMessage = document.getElementById('errorMessage');
        loadingIndicator = document.getElementById('loadingIndicator');
        resultsSection = document.getElementById('resultsSection');
        resultsContainer = document.getElementById('resultsContainer');
        termsCategories = document.getElementById('termsCategories');  // Added for terms display
        
        // Verify all elements exist
        if (!pdfFile || !extractBtn) {
            console.error('Required DOM elements not found');
            return;
        }
        
        setupEventListeners();
        setupExtractionTypeListener();
        
        // Load only lightweight stats (not full database) - deferred
        setTimeout(() => {
            try {
                loadDatabaseStatsLight();
            } catch (e) {
                console.warn('Failed to load database stats:', e);
            }
        }, 500);
    } catch (error) {
        console.error('Initialization error:', error);
    }
});

// Setup extraction type change listener
function setupExtractionTypeListener() {
    const extractionRadios = document.querySelectorAll('input[name="extractionType"]');
    extractionRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const languageDiv = document.getElementById('languageSelectionDiv');
            const hyperlinkDiv = document.getElementById('hyperlinkOptionsDiv');
            const specComparerOptionsDiv = document.getElementById('specComparerOptionsDiv');
            
            // Hide all option divs first
            languageDiv.style.display = 'none';
            hyperlinkDiv.style.display = 'none';
            if (specComparerOptionsDiv) specComparerOptionsDiv.style.display = 'none';
            
            // Show/hide based on selection
            if (this.value === 'multilingual') {
                languageDiv.style.display = 'block';
            } else if (this.value === 'hyperlinks') {
                hyperlinkDiv.style.display = 'block';
            } else if (this.value === 'spec_compare') {
                if (specComparerOptionsDiv) specComparerOptionsDiv.style.display = 'block';
            }
        });
    });
}

// Setup calculator type change listener
// Event Listeners
function setupEventListeners() {
    // File input change - NO debounce for file selection
    if (pdfFile) {
        pdfFile.addEventListener('change', handleFileSelect);
    } else {
        console.error('pdfFile element not found');
    }

    // Drag and drop
    const fileLabel = document.querySelector('.file-label');
    if (fileLabel) {
        fileLabel.addEventListener('dragover', handleDragOver);
        fileLabel.addEventListener('dragleave', handleDragLeave);
        fileLabel.addEventListener('drop', handleDrop);
    }

    // Extract button
    if (extractBtn) {
        extractBtn.addEventListener('click', handleExtract);
    } else {
        console.error('extractBtn element not found');
    }

    // Download buttons
    if (downloadFullBtn) {
        downloadFullBtn.addEventListener('click', debounce(handleDownloadFull, 500));
    }
    if (downloadReportBtn) {
        downloadReportBtn.addEventListener('click', debounce(handleDownloadReport, 500));
    }

    // Escape key cancels current operation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isProcessing) {
            cancelOperation();
        }
    });
}

// Debounce function
function debounce(func, wait) {
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(debounceTimer);
            func(...args);
        };
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(later, wait);
    };
}

// File Selection (Optimized with validation)
function handleFileSelect(event) {
    console.log('📁 File selection event triggered');
    
    const files = event.target.files;
    if (!files || files.length === 0) {
        console.warn('No files selected');
        return;
    }

    const file = files[0];
    console.log('📄 File selected:', file.name, `(${formatFileSize(file.size)})`);
    
    // Validate file type and size (max 50MB)
    const MAX_FILE_SIZE = 50 * 1024 * 1024;
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    
    if (!isPdf) {
        console.error('Invalid file type:', file.type);
        showError('❌ Please select a valid PDF file');
        resetFileSelection();
        return;
    }

    if (file.size > MAX_FILE_SIZE) {
        console.error('File too large:', file.size);
        showError(`❌ File size exceeds 50MB limit (current: ${formatFileSize(file.size)})`);
        resetFileSelection();
        return;
    }

    selectedFile = file;
    updateFileDisplay();
    enableButtons();
    errorMessage.style.display = 'none';
    console.log('✓ File validated and ready for extraction');
}

function resetFileSelection() {
    selectedFile = null;
    pdfFile.value = '';
    fileName.textContent = '';
    fileName.classList.remove('show');
    disableButtons();
}

function updateFileDisplay() {
    const sizeStr = formatFileSize(selectedFile.size);
    const displayText = `✓ Selected: ${selectedFile.name} (${sizeStr})`;
    fileName.textContent = displayText;
    fileName.classList.add('show');
    console.log('📍 File display updated:', displayText);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// Drag and Drop
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.style.borderColor = '#2563eb';
    event.currentTarget.style.backgroundColor = '#f0f7ff';
}

function handleDragLeave(event) {
    event.currentTarget.style.borderColor = '#e5e7eb';
    event.currentTarget.style.backgroundColor = '';
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
            selectedFile = file;
            pdfFile.files = event.dataTransfer.files;
            updateFileDisplay();
            enableButtons();
        } else {
            showError('Please drop a valid PDF file');
        }
    }
    
    event.currentTarget.style.borderColor = '#e5e7eb';
    event.currentTarget.style.backgroundColor = '';
}

// Button States
function enableButtons() {
    extractBtn.disabled = false;
    downloadFullBtn.disabled = false;
    downloadReportBtn.disabled = false;
    console.log('✓ Extract buttons enabled');
}

function disableButtons() {
    extractBtn.disabled = true;
    downloadFullBtn.disabled = true;
    downloadReportBtn.disabled = true;
    console.log('✓ Extract buttons disabled');
}

// Extract Handler (Optimized with chunked processing for 100k database)
function handleExtract() {
    if (!selectedFile) {
        showError('No file selected');
        return;
    }

    if (isProcessing) {
        showError('Processing already in progress. Please wait.');
        return;
    }

    const extractionType = document.querySelector('input[name="extractionType"]:checked').value;
    
    // For multilingual, handle differently
    if (extractionType === 'multilingual') {
        handleMultilingualExtract();
        return;
    }
    
    // For hyperlinks, handle separately
    if (extractionType === 'hyperlinks') {
        handleHyperlinkExtract();
        return;
    }
    
    // For spec comparer pro, handle separately
    if (extractionType === 'spec_compare') {
        handleSpecCompare();
        return;
    }
    
    showLoading(`📊 Processing with 100k terms database...`);
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';
    errorMessage.style.display = 'none';
    isProcessing = true;
    extractBtn.disabled = true;
    processingAborted = false;

    // Create abort controller for cancellation
    abortController = new AbortController();

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('type', extractionType);

    PERF_METRICS.requestStart = performance.now();

    fetch('/api/upload', {
        method: 'POST',
        body: formData,
        signal: abortController.signal,
        timeout: CONFIG.REQUEST_TIMEOUT
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const elapsed = performance.now() - PERF_METRICS.requestStart;
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
        
        if (data.error) {
            showError(data.error);
        } else {
            lastExtractedFilename = data.filename;
            showSuccess(`✓ Processed in ${(elapsed/1000).toFixed(2)}s`);
            // Use chunked rendering for large results
            displayResultsChunked(data, extractionType);
        }
    })
    .catch(error => {
        if (error.name === 'AbortError') {
            showError('⏹️ Operation cancelled by user');
        } else {
            showError(`Error: ${error.message}`);
        }
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
    });
}

// Chunked Results Display (prevents frontend lag)
function displayResultsChunked(data, type) {
    resultsContainer.innerHTML = '';
    
    // Use proper display functions based on type
    if (type === 'text') {
        displayTextResults(data);
    } else if (type === 'analysis') {
        displayAnalysisResults(data);
    } else if (type === 'sections') {
        displaySectionsResults(data);
    } else {
        // Fallback: render as chunked sections
        const sections = [];
        if (data.data) sections.push({ title: '📄 Extracted Text', content: data.data });
        if (data.text) sections.push({ title: '📄 Extracted Text', content: data.text });
        if (data.tables) sections.push({ title: '📊 Tables', content: JSON.stringify(data.tables, null, 2) });
        if (data.analysis) sections.push({ title: '📈 RFP Analysis', content: JSON.stringify(data.analysis, null, 2) });
        
        if (sections.length > 0) {
            renderSectionsChunked(sections, 0);
        }
    }
}

// Render sections in chunks
function renderSectionsChunked(sections, index) {
    if (index >= sections.length || processingAborted) return;
    
    const section = sections[index];
    const div = document.createElement('div');
    div.className = 'result-section';
    div.innerHTML = `<h3>${section.title}</h3>`;
    
    // Render content in chunks if large
    if (section.content && section.content.length > CONFIG.CHUNK_SIZE) {
        const textarea = document.createElement('textarea');
        textarea.value = section.content.substring(0, CONFIG.CHUNK_SIZE) + '...';
        textarea.rows = 10;
        textarea.readOnly = true;
        div.appendChild(textarea);
        
        // Add "load more" button for large content
        const loadMoreBtn = document.createElement('button');
        loadMoreBtn.textContent = '📖 Load Full Content';
        loadMoreBtn.className = 'btn btn-secondary';
        loadMoreBtn.onclick = () => {
            textarea.value = section.content;
            loadMoreBtn.style.display = 'none';
        };
        div.appendChild(loadMoreBtn);
    } else {
        const textarea = document.createElement('textarea');
        textarea.value = section.content;
        textarea.rows = Math.min(15, Math.ceil(section.content.length / 80));
        textarea.readOnly = true;
        div.appendChild(textarea);
    }
    
    resultsContainer.appendChild(div);
    
    // Schedule next section render to keep UI responsive
    requestAnimationFrame(() => {
        renderSectionsChunked(sections, index + 1);
    });
}

// Multilingual Extract Handler
function handleMultilingualExtract() {
    showLoading();
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';
    errorMessage.style.display = 'none';
    isProcessing = true;
    extractBtn.disabled = true;

    // Create abort controller for cancellation
    requestAbortController = new AbortController();

    const formData = new FormData();
    formData.append('file', selectedFile);

    fetch('/api/analyze-multilingual', {
        method: 'POST',
        body: formData,
        signal: requestAbortController.signal
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
        
        if (data.error) {
            showError(data.error);
        } else {
            lastExtractedFilename = data.filename;
            displayMultilingualResults(data);
        }
    })
    .catch(error => {
        if (error.name === 'AbortError') {
            showError('Operation cancelled');
        } else {
            showError(`Error: ${error.message}`);
        }
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
    });
}

// Hyperlink Extract Handler
function handleHyperlinkExtract() {
    // Get options
    const includeLargeFiles = document.getElementById('includeLargeFiles')?.checked || false;
    const skipDuplicates = document.getElementById('skipDuplicates')?.checked || true;
    
    // Update loading message based on options
    const loadingMsg = includeLargeFiles 
        ? '🔗 Extracting hyperlinks (including large files - this may take a while)...'
        : '🔗 Extracting hyperlinks from PDF...';
    
    showLoading(loadingMsg);
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';
    errorMessage.style.display = 'none';
    isProcessing = true;
    extractBtn.disabled = true;
    
    // Show progress bar for hyperlink extraction
    const progressDiv = document.getElementById('downloadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    if (progressDiv) {
        progressDiv.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = 'Starting download...';
    }

    // Create abort controller for cancellation
    requestAbortController = new AbortController();

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('include_large_files', includeLargeFiles ? 'true' : 'false');
    formData.append('skip_duplicates', skipDuplicates ? 'true' : 'false');

    PERF_METRICS.requestStart = performance.now();
    
    // Simulate progress updates
    let progressInterval = null;
    let estimatedTotal = 100;
    let currentProgress = 0;
    
    progressInterval = setInterval(() => {
        if (currentProgress < 95) {
            currentProgress += Math.random() * 5;
            if (progressBar) progressBar.style.width = `${Math.min(currentProgress, 95)}%`;
            
            const elapsed = (performance.now() - PERF_METRICS.requestStart) / 1000;
            const eta = currentProgress > 10 ? ((elapsed / currentProgress) * (100 - currentProgress)).toFixed(0) : '--';
            if (progressText) progressText.textContent = `Downloading files... ETA: ${eta}s`;
        }
    }, 500);

    fetch('/api/extract-hyperlinks', {
        method: 'POST',
        body: formData,
        signal: requestAbortController.signal
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        clearInterval(progressInterval);
        if (progressBar) progressBar.style.width = '100%';
        if (progressText) progressText.textContent = 'Complete!';
        
        const elapsed = performance.now() - PERF_METRICS.requestStart;
        setTimeout(() => {
            hideLoading();
            if (progressDiv) progressDiv.style.display = 'none';
        }, 500);
        
        isProcessing = false;
        extractBtn.disabled = false;
        
        if (data.error) {
            showError(data.error);
        } else {
            showSuccess(`✓ Downloaded ${data.downloaded_count}/${data.total_links} files in ${(elapsed/1000).toFixed(1)}s`);
            displayHyperlinkResults(data);
        }
    })
    .catch(error => {
        clearInterval(progressInterval);
        if (progressDiv) progressDiv.style.display = 'none';
        
        if (error.name === 'AbortError') {
            showError('Operation cancelled');
        } else {
            showError(`Error: ${error.message}`);
        }
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
    });
}

// Spec Comparer Handler
function handleSpecCompare() {
    showLoading('🔌 Analyzing RFP with Spec Comparer Pro...');
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';
    errorMessage.style.display = 'none';
    isProcessing = true;
    extractBtn.disabled = true;

    // Create abort controller for cancellation
    requestAbortController = new AbortController();

    const formData = new FormData();
    formData.append('file', selectedFile);
    
    // Get analysis options from checkboxes
    const includeCalculations = document.getElementById('includeCalculations')?.checked ?? true;
    const includeRecommendations = document.getElementById('includeRecommendations')?.checked ?? true;
    const includeBudgetAnalysis = document.getElementById('includeBudgetAnalysis')?.checked ?? true;
    const includeOemComparison = document.getElementById('includeOemComparison')?.checked ?? true;
    const cableLength = document.getElementById('analysisLength')?.value || 100;
    const application = document.getElementById('analysisApplication')?.value || 'auto';
    
    // Add analysis options to form
    formData.append('include_calculations', includeCalculations);
    formData.append('include_recommendations', includeRecommendations);
    formData.append('include_budget', includeBudgetAnalysis);
    formData.append('include_oem_comparison', includeOemComparison);
    formData.append('cable_length', cableLength);
    formData.append('application', application);

    PERF_METRICS.requestStart = performance.now();

    fetch('/api/spec-compare', {
        method: 'POST',
        body: formData,
        signal: requestAbortController.signal
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const elapsed = performance.now() - PERF_METRICS.requestStart;
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
        
        if (data.error) {
            showError(data.error);
        } else {
            const matchCount = data.comparisons ? data.comparisons.reduce((sum, c) => sum + c.match_count, 0) : 0;
            showSuccess(`✓ Found ${data.total_requirements} requirements, ${matchCount} product matches in ${(elapsed/1000).toFixed(2)}s`);
            displaySpecCompareResults(data);
        }
    })
    .catch(error => {
        if (error.name === 'AbortError') {
            showError('Operation cancelled');
        } else {
            showError(`Error: ${error.message}`);
        }
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
    });
}

// Spec Calculator Handler (No file upload needed)
function handleSpecCalculator() {
    const calcType = document.querySelector('input[name="calcType"]:checked').value;
    
    showLoading(`🧮 Calculating ${calcType.replace('_', ' ')}...`);
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';
    errorMessage.style.display = 'none';
    isProcessing = true;
    extractBtn.disabled = true;

    PERF_METRICS.requestStart = performance.now();

    // Build request data based on calculation type
    let requestData = { calculation_type: calcType };
    
    if (calcType === 'cable_sizing') {
        requestData = {
            ...requestData,
            load_current: parseFloat(document.getElementById('loadCurrent').value),
            voltage: parseFloat(document.getElementById('systemVoltage').value),
            material: document.getElementById('conductorMaterial').value,
            installation: document.getElementById('installationMethod').value,
            ambient_temp: parseInt(document.getElementById('ambientTemp').value),
            cable_grouping: parseInt(document.getElementById('cableGrouping').value),
            safety_factor: parseFloat(document.getElementById('safetyFactor').value)
        };
    } else if (calcType === 'voltage_drop') {
        requestData = {
            ...requestData,
            cable_size: parseFloat(document.getElementById('vdCableSize').value),
            length: parseFloat(document.getElementById('cableLength').value),
            current: parseFloat(document.getElementById('vdCurrent').value),
            material: document.getElementById('conductorMaterial').value,
            voltage: parseFloat(document.getElementById('vdVoltage').value),
            power_factor: parseFloat(document.getElementById('powerFactor').value),
            cores: parseInt(document.getElementById('vdCores').value)
        };
    } else if (calcType === 'short_circuit') {
        requestData = {
            ...requestData,
            cable_size: parseFloat(document.getElementById('scCableSize').value),
            material: document.getElementById('scMaterial').value,
            fault_duration: parseFloat(document.getElementById('faultDuration').value)
        };
    } else if (calcType === 'power_capacity') {
        requestData = {
            ...requestData,
            cable_size: parseFloat(document.getElementById('pcCableSize').value),
            material: document.getElementById('pcMaterial').value,
            voltage: parseFloat(document.getElementById('pcVoltage').value),
            cores: parseInt(document.getElementById('pcCores').value),
            power_factor: parseFloat(document.getElementById('pcPowerFactor').value),
            installation: document.getElementById('pcInstallation').value
        };
    }

    fetch('/api/spec-calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const elapsed = performance.now() - PERF_METRICS.requestStart;
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
        
        if (data.error) {
            showError(data.error);
        } else {
            showSuccess(`✓ Calculation complete in ${(elapsed/1000).toFixed(2)}s`);
            displaySpecCalculatorResults(data);
        }
    })
    .catch(error => {
        showError(`Error: ${error.message}`);
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
    });
}

// Product Recommender Handler (No file upload needed)
function handleProductRecommender() {
    const recommendType = document.querySelector('input[name="recommendType"]:checked').value;
    
    showLoading(`🎯 Getting ${recommendType.replace('_', ' ')} recommendations...`);
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';
    errorMessage.style.display = 'none';
    isProcessing = true;
    extractBtn.disabled = true;

    PERF_METRICS.requestStart = performance.now();

    // Build request data based on recommendation type
    let requestData = { recommend_type: recommendType };
    
    if (recommendType === 'by_application') {
        const conductorSize = document.getElementById('appConductorSize').value;
        const cores = document.getElementById('appCores').value;
        requestData = {
            ...requestData,
            application: document.getElementById('applicationType').value,
            conductor_size: conductorSize ? parseFloat(conductorSize) : null,
            cores: cores ? parseInt(cores) : null
        };
    } else if (recommendType === 'by_budget') {
        requestData = {
            ...requestData,
            budget_category: document.getElementById('budgetCategory').value,
            conductor_size: parseFloat(document.getElementById('budgetConductorSize').value),
            cores: parseInt(document.getElementById('budgetCores').value),
            material: document.getElementById('budgetMaterial').value,
            length_meters: parseFloat(document.getElementById('budgetLength').value)
        };
    } else if (recommendType === 'best_quality') {
        const conductorSize = document.getElementById('qualityConductorSize').value;
        const cores = document.getElementById('qualityCores').value;
        const insulation = document.getElementById('qualityInsulation').value;
        requestData = {
            ...requestData,
            conductor_size: conductorSize ? parseFloat(conductorSize) : null,
            cores: cores ? parseInt(cores) : null,
            insulation: insulation || null
        };
    } else if (recommendType === 'compare_oems') {
        requestData = {
            ...requestData,
            conductor_size: parseFloat(document.getElementById('compareConductorSize').value),
            cores: parseInt(document.getElementById('compareCores').value),
            material: document.getElementById('compareMaterial').value
        };
    }

    fetch('/api/product-recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const elapsed = performance.now() - PERF_METRICS.requestStart;
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
        
        if (data.error) {
            showError(data.error);
        } else {
            const count = data.recommendations?.length || data.oem_comparison?.length || 0;
            showSuccess(`✓ Found ${count} recommendations in ${(elapsed/1000).toFixed(2)}s`);
            displayProductRecommenderResults(data);
        }
    })
    .catch(error => {
        showError(`Error: ${error.message}`);
        hideLoading();
        isProcessing = false;
        extractBtn.disabled = false;
    });
}

// Display Spec Calculator Results
function displaySpecCalculatorResults(data) {
    resultsContainer.innerHTML = '';
    
    const calcType = data.calculation_type;
    const input = data.input || {};
    const calculation = data.calculation || {};
    
    // Header
    const calcTypeLabels = {
        'cable_sizing': '📏 Cable Sizing Results',
        'voltage_drop': '⚡ Voltage Drop Analysis',
        'short_circuit': '💥 Short Circuit Capacity',
        'power_capacity': '🔋 Power Capacity Analysis'
    };
    
    let html = `
        <div class="calculator-results">
            <div class="calc-result-header">
                <h3>${calcTypeLabels[calcType] || 'Calculation Results'}</h3>
            </div>
    `;
    
    // Input Parameters Section
    html += `
        <div class="result-section">
            <h4>📋 Input Parameters</h4>
            <div class="result-grid">
                ${Object.entries(input).map(([key, value]) => `
                    <div class="result-item">
                        <div class="label">${formatLabel(key)}</div>
                        <div class="value">${formatValue(key, value)}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    // Derating Factors (for cable sizing)
    if (data.derating_factors) {
        const df = data.derating_factors;
        html += `
            <div class="result-section">
                <h4>📉 Derating Factors Applied</h4>
                <div class="result-grid">
                    <div class="result-item">
                        <div class="label">Temperature</div>
                        <div class="value">${df.temperature}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">Grouping</div>
                        <div class="value">${df.grouping}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">Installation</div>
                        <div class="value">${df.installation}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">Total Derating</div>
                        <div class="value highlight">${df.total}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Main Calculation Results
    html += `
        <div class="result-section">
            <h4>📊 Calculation Results</h4>
            <div class="result-grid">
    `;
    
    if (calcType === 'cable_sizing') {
        html += `
            <div class="result-item">
                <div class="label">Required Capacity</div>
                <div class="value">${calculation.required_capacity}<span class="unit">A</span></div>
            </div>
            <div class="result-item">
                <div class="label">Recommended Size</div>
                <div class="value highlight">${calculation.recommended_size}<span class="unit">sq mm</span></div>
            </div>
            <div class="result-item">
                <div class="label">Cable Capacity (Base)</div>
                <div class="value">${calculation.recommended_capacity}<span class="unit">A</span></div>
            </div>
            <div class="result-item">
                <div class="label">Derated Capacity</div>
                <div class="value">${calculation.derated_capacity}<span class="unit">A</span></div>
            </div>
            <div class="result-item">
                <div class="label">Utilization</div>
                <div class="value ${calculation.utilization_percent > 80 ? 'warning' : ''}">${calculation.utilization_percent}<span class="unit">%</span></div>
            </div>
        `;
        
        if (data.alternative) {
            html += `
                </div>
            </div>
            <div class="result-section">
                <h4>🔄 Alternative (Next Size Up)</h4>
                <div class="result-grid">
                    <div class="result-item">
                        <div class="label">Next Size</div>
                        <div class="value">${data.alternative.next_size_up}<span class="unit">sq mm</span></div>
                    </div>
                    <div class="result-item">
                        <div class="label">Capacity</div>
                        <div class="value">${data.alternative.next_capacity}<span class="unit">A</span></div>
                    </div>
                    <div class="result-item">
                        <div class="label">Derated</div>
                        <div class="value">${data.alternative.next_derated}<span class="unit">A</span></div>
                    </div>
            `;
        }
    } else if (calcType === 'voltage_drop') {
        const status = calculation.assessment;
        const statusClass = status === 'acceptable' ? 'highlight' : status === 'warning' ? 'warning' : 'danger';
        
        html += `
            <div class="result-item">
                <div class="label">Resistance</div>
                <div class="value">${calculation.resistance}<span class="unit">Ω</span></div>
            </div>
            <div class="result-item">
                <div class="label">Voltage Drop</div>
                <div class="value ${statusClass}">${calculation.voltage_drop_volts}<span class="unit">V</span></div>
            </div>
            <div class="result-item">
                <div class="label">Voltage Drop %</div>
                <div class="value ${statusClass}">${calculation.voltage_drop_percent}<span class="unit">%</span></div>
            </div>
            <div class="result-item">
                <div class="label">Receiving End Voltage</div>
                <div class="value">${calculation.receiving_end_voltage}<span class="unit">V</span></div>
            </div>
            <div class="result-item">
                <div class="label">Status</div>
                <div class="value"><span class="status-badge ${status}">${status.toUpperCase()}</span></div>
            </div>
        `;
        
        // Standards compliance
        if (data.standards) {
            html += `
                </div>
            </div>
            <div class="result-section">
                <h4>📜 IS 732 Compliance</h4>
                <div class="result-grid">
                    <div class="result-item">
                        <div class="label">Feeder Circuit (≤5%)</div>
                        <div class="value">${data.standards.compliant_feeder ? '✅ Compliant' : '❌ Non-compliant'}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">Branch Circuit (≤3%)</div>
                        <div class="value">${data.standards.compliant_branch ? '✅ Compliant' : '❌ Non-compliant'}</div>
                    </div>
            `;
        }
        
        // Recommendations
        if (data.recommendations && data.recommendations.length > 0) {
            html += `
                </div>
            </div>
            <div class="result-section">
                <h4>💡 Recommendations</h4>
                <ul class="recommendations-list">
                    ${data.recommendations.map(r => `<li>${r}</li>`).join('')}
                </ul>
            `;
        }
    } else if (calcType === 'short_circuit') {
        html += `
            <div class="result-item">
                <div class="label">K Factor</div>
                <div class="value">${calculation.k_factor}</div>
            </div>
            <div class="result-item">
                <div class="label">I²t Rating</div>
                <div class="value">${calculation.i2t_rating}<span class="unit">MA²s</span></div>
            </div>
            <div class="result-item">
                <div class="label">SC Current (0.1s)</div>
                <div class="value highlight">${calculation.withstand_current_0_1s_kA || calculation['withstand_current_0.1s_kA']}<span class="unit">kA</span></div>
            </div>
            <div class="result-item">
                <div class="label">SC Current (0.5s)</div>
                <div class="value">${calculation.withstand_current_0_5s_kA || calculation['withstand_current_0.5s_kA']}<span class="unit">kA</span></div>
            </div>
            <div class="result-item">
                <div class="label">SC Current (1.0s)</div>
                <div class="value">${calculation.withstand_current_1s_kA}<span class="unit">kA</span></div>
            </div>
        `;
        
        if (data.notes && data.notes.length > 0) {
            html += `
                </div>
            </div>
            <div class="result-section">
                <h4>ℹ️ Notes</h4>
                <ul class="notes-list">
                    ${data.notes.map(n => `<li>${n}</li>`).join('')}
                </ul>
            `;
        }
    } else if (calcType === 'power_capacity') {
        html += `
            <div class="result-item">
                <div class="label">Base Current Capacity</div>
                <div class="value">${calculation.base_current_capacity}<span class="unit">A</span></div>
            </div>
            <div class="result-item">
                <div class="label">Derated Current</div>
                <div class="value">${calculation.derated_current_capacity}<span class="unit">A</span></div>
            </div>
            <div class="result-item">
                <div class="label">Power Capacity (kW)</div>
                <div class="value highlight">${calculation.power_capacity_kW}<span class="unit">kW</span></div>
            </div>
            <div class="result-item">
                <div class="label">Power Capacity (kVA)</div>
                <div class="value">${calculation.power_capacity_kVA}<span class="unit">kVA</span></div>
            </div>
            <div class="result-item">
                <div class="label">Derating Applied</div>
                <div class="value">${calculation.derating_applied}</div>
            </div>
        `;
        
        if (data.recommendations) {
            html += `
                </div>
            </div>
            <div class="result-section">
                <h4>🎯 Suitable For</h4>
                <div class="result-grid">
                    <div class="result-item">
                        <div class="label">Motor Load</div>
                        <div class="value">${data.recommendations.suitable_for_motor}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">Resistive Load</div>
                        <div class="value">${data.recommendations.suitable_for_load}</div>
                    </div>
            `;
        }
    }
    
    html += `
            </div>
        </div>
    </div>`;
    
    resultsContainer.innerHTML = html;
}

// Display Product Recommender Results
function displayProductRecommenderResults(data) {
    resultsContainer.innerHTML = '';
    
    const recommendType = data.recommend_type;
    
    let html = `<div class="calculator-results">`;
    
    // Header based on type
    const typeHeaders = {
        'by_application': `🏢 Application-Based Recommendations`,
        'by_budget': `💰 Budget-Based Recommendations`,
        'best_quality': `⭐ Top Quality Products`,
        'compare_oems': `🏭 OEM Comparison`
    };
    
    html += `
        <div class="calc-result-header">
            <h3>${typeHeaders[recommendType] || 'Product Recommendations'}</h3>
        </div>
    `;
    
    // Application profile info
    if (recommendType === 'by_application' && data.profile) {
        html += `
            <div class="app-profile-card">
                <h4>📋 ${data.application.charAt(0).toUpperCase() + data.application.slice(1)} Application Profile</h4>
                <p>${data.profile.description}</p>
                <div class="app-profile-tags">
                    <span class="app-profile-tag">Preferred: ${data.profile.preferred_insulation.join(', ')}</span>
                    <span class="app-profile-tag">${data.profile.armoured ? '🛡️ Armoured' : 'Unarmoured'}</span>
                    ${data.profile.fire_rating_required ? '<span class="app-profile-tag">🔥 Fire Rated</span>' : ''}
                </div>
            </div>
        `;
    }
    
    // Budget info
    if (recommendType === 'by_budget' && data.filters) {
        html += `
            <div class="app-profile-card">
                <h4>💰 Budget: ${data.budget_category.charAt(0).toUpperCase() + data.budget_category.slice(1)}</h4>
                <p>${data.budget_info?.description || ''}</p>
                <div class="app-profile-tags">
                    <span class="app-profile-tag">Size: ${data.filters.conductor_size} sq mm</span>
                    <span class="app-profile-tag">Cores: ${data.filters.cores}</span>
                    <span class="app-profile-tag">Length: ${data.filters.length_meters}m</span>
                    <span class="app-profile-tag">Max Budget: ₹${data.filters.max_budget}</span>
                </div>
            </div>
        `;
    }
    
    // OEM Comparison
    if (recommendType === 'compare_oems' && data.oem_comparison) {
        html += `
            <div class="result-section">
                <h4>📊 Specification: ${data.specification.conductor_size} sq mm × ${data.specification.cores} Core ${data.specification.material}</h4>
                <p style="color: #94a3b8; margin-bottom: 16px;">Comparing ${data.oems_compared} OEMs, ${data.total_products} total products</p>
                
                <table class="oem-comparison-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>OEM</th>
                            <th>Best Product</th>
                            <th>Price Range</th>
                            <th>Quality</th>
                            <th>Warranty</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.oem_comparison.map((oem, idx) => `
                            <tr>
                                <td><span class="oem-rank rank-${idx + 1}">${idx + 1}</span></td>
                                <td style="font-weight: 600; color: #818cf8;">${oem.oem}</td>
                                <td>${oem.best_product?.product_name || '-'}</td>
                                <td>₹${oem.pricing?.min_price || '-'} - ₹${oem.pricing?.max_price || '-'}</td>
                                <td>${oem.quality?.overall_score || '-'}/100</td>
                                <td>${oem.quality?.warranty_years || '-'} yrs</td>
                                <td style="font-weight: 700; color: #22c55e;">${oem.overall_score}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                
                <div style="margin-top: 16px; display: flex; gap: 24px; color: #94a3b8; font-size: 0.9rem;">
                    <span>🏆 Best Value: <strong style="color: #ffd700;">${data.best_value}</strong></span>
                    <span>💰 Price Range: <strong style="color: #22c55e;">₹${data.price_range?.min} - ₹${data.price_range?.max}</strong></span>
                    <span>📊 Average: <strong style="color: #818cf8;">₹${data.price_range?.avg}/m</strong></span>
                </div>
            </div>
        `;
    }
    
    // Recommendations list
    const recommendations = data.recommendations || [];
    if (recommendations.length > 0) {
        html += `<div class="result-section"><h4>🎯 Top Recommendations (${recommendations.length})</h4>`;
        
        recommendations.forEach((rec, idx) => {
            const rankClass = idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : '';
            const scoreValue = rec.application_score || rec.value_score || rec.quality_score || 0;
            const scoreClass = scoreValue >= 70 ? 'excellent' : scoreValue >= 50 ? 'good' : 'fair';
            
            html += `
                <div class="recommend-card ${rankClass}">
                    <div class="recommend-header">
                        <div>
                            <div class="recommend-oem">${rec.oem}</div>
                            <div class="recommend-name">${rec.product_name || rec.product_code}</div>
                            ${rec.product_code ? `<div style="color: #64748b; font-size: 0.8rem;">${rec.product_code}</div>` : ''}
                        </div>
                        <div class="recommend-score ${scoreClass}">${scoreValue.toFixed(1)}%</div>
                    </div>
                    
                    <div class="recommend-specs">
                        ${rec.specs ? `
                            ${rec.specs.conductor_size ? `<div class="recommend-spec-item"><span class="spec-label">Size</span><span class="spec-value">${rec.specs.conductor_size} sq mm</span></div>` : ''}
                            ${rec.specs.cores ? `<div class="recommend-spec-item"><span class="spec-label">Cores</span><span class="spec-value">${rec.specs.cores}</span></div>` : ''}
                            ${rec.specs.insulation ? `<div class="recommend-spec-item"><span class="spec-label">Insulation</span><span class="spec-value">${rec.specs.insulation}</span></div>` : ''}
                            ${rec.specs.voltage ? `<div class="recommend-spec-item"><span class="spec-label">Voltage</span><span class="spec-value">${rec.specs.voltage}</span></div>` : ''}
                            ${rec.specs.material ? `<div class="recommend-spec-item"><span class="spec-label">Material</span><span class="spec-value">${rec.specs.material}</span></div>` : ''}
                            ${rec.specs.current_rating ? `<div class="recommend-spec-item"><span class="spec-label">Current</span><span class="spec-value">${rec.specs.current_rating} A</span></div>` : ''}
                        ` : ''}
                    </div>
                    
                    ${rec.pricing || rec.price_per_meter ? `
                        <div style="padding: 12px 0; border-top: 1px solid #334155; border-bottom: 1px solid #334155; margin: 12px 0;">
                            <span style="color: #64748b; font-size: 0.85rem;">Price: </span>
                            <span style="color: #22c55e; font-weight: 700; font-size: 1.1rem;">₹${rec.pricing?.price_per_meter || rec.price_per_meter}/m</span>
                            ${rec.pricing?.total_cost ? `<span style="color: #94a3b8; margin-left: 16px;">Total: ₹${rec.pricing.total_cost} for ${rec.pricing.length_meters}m</span>` : ''}
                        </div>
                    ` : ''}
                    
                    ${rec.quality ? `
                        <div style="display: flex; gap: 16px; margin-bottom: 12px; font-size: 0.85rem;">
                            ${rec.quality.overall_score ? `<span style="color: #94a3b8;">Quality: <strong style="color: #e2e8f0;">${rec.quality.overall_score}/100</strong></span>` : ''}
                            ${rec.quality.warranty_years ? `<span style="color: #94a3b8;">Warranty: <strong style="color: #e2e8f0;">${rec.quality.warranty_years} yrs</strong></span>` : ''}
                            ${rec.quality.fire_rating ? `<span style="color: #94a3b8;">Fire: <strong style="color: #e2e8f0;">${rec.quality.fire_rating}</strong></span>` : ''}
                        </div>
                    ` : ''}
                    
                    ${(rec.why_suitable || rec.why_recommended || rec.why_top_quality) ? `
                        <div class="recommend-reasons">
                            <h5>Why Recommended:</h5>
                            <ul>
                                ${(rec.why_suitable || rec.why_top_quality || [rec.why_recommended]).filter(r => r).map(reason => 
                                    Array.isArray(reason) ? reason.map(r => `<li>${r}</li>`).join('') : `<li>${reason}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        html += `</div>`;
    }
    
    if (recommendations.length === 0 && (!data.oem_comparison || data.oem_comparison.length === 0)) {
        html += `
            <div class="result-section" style="text-align: center; padding: 40px;">
                <p style="font-size: 1.2rem; color: #94a3b8;">⚠️ No products found matching your criteria</p>
                <p style="color: #64748b;">Try adjusting the filters or selecting different parameters</p>
            </div>
        `;
    }
    
    html += `</div>`;
    resultsContainer.innerHTML = html;
}

// Helper function to format labels
function formatLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Helper function to format values
function formatValue(key, value) {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (key.includes('voltage')) return `${value} V`;
    if (key.includes('current')) return `${value} A`;
    if (key.includes('temp')) return `${value}°C`;
    if (key.includes('factor')) return value;
    return value;
}

// Display Spec Compare Results
function displaySpecCompareResults(data) {
    resultsContainer.innerHTML = '';
    
    const comparisons = data.comparisons || [];
    const dbInfo = data.database_info || {};
    const analysisOptions = data.analysis_options || {};
    const oemSummary = data.oem_summary || null;
    const detectedApp = data.detected_application || 'commercial';
    
    // Application type display
    const appDisplayNames = {
        'residential': '🏠 Residential',
        'commercial': '🏢 Commercial',
        'industrial': '🏭 Industrial',
        'hospital': '🏥 Hospital',
        'data_center': '🖥️ Data Center',
        'high_rise': '🏗️ High Rise',
        'underground': '⬇️ Underground',
        'outdoor': '☀️ Outdoor'
    };
    
    // Header with enhanced stats
    const headerHtml = `
        <div class="spec-compare-header" style="margin-bottom: 24px; padding: 20px; background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); border-radius: 16px; color: white; border: 1px solid #4338ca;">
            <h3 style="margin: 0 0 12px 0; font-size: 1.4rem;">🔌 Spec Comparer Pro Results</h3>
            <div style="display: flex; gap: 24px; flex-wrap: wrap; font-size: 0.95rem; margin-bottom: 12px;">
                <div><strong style="color: #a5b4fc;">${data.total_requirements || 0}</strong> Requirements Found</div>
                <div><strong style="color: #a5b4fc;">${dbInfo.total_products || 0}</strong> Products in Database</div>
                <div><strong style="color: #a5b4fc;">${(dbInfo.oems || []).length}</strong> OEMs</div>
                <div>🎯 Detected: <span style="color: #c4b5fd;">${appDisplayNames[detectedApp] || detectedApp}</span></div>
            </div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap; font-size: 0.8rem;">
                ${analysisOptions.calculations_included ? '<span style="padding: 4px 8px; background: rgba(34, 197, 94, 0.2); border-radius: 4px; color: #4ade80;">✓ Voltage/Power Calculations</span>' : ''}
                ${analysisOptions.recommendations_included ? '<span style="padding: 4px 8px; background: rgba(34, 197, 94, 0.2); border-radius: 4px; color: #4ade80;">✓ Smart Recommendations</span>' : ''}
                ${analysisOptions.budget_included ? '<span style="padding: 4px 8px; background: rgba(34, 197, 94, 0.2); border-radius: 4px; color: #4ade80;">✓ Budget Analysis</span>' : ''}
                <span style="padding: 4px 8px; background: rgba(129, 140, 248, 0.2); border-radius: 4px; color: #a5b4fc;">📏 ${analysisOptions.cable_length || 100}m Cable Length</span>
            </div>
        </div>
    `;
    
    if (comparisons.length === 0) {
        resultsContainer.innerHTML = headerHtml + `
            <div class="no-results" style="text-align: center; padding: 50px; background: #1e1b4b; border-radius: 16px; border: 1px solid #4338ca;">
                <p style="font-size: 1.2rem; color: #e2e8f0; margin-bottom: 12px;">⚠️ No wire/cable specifications found in the RFP</p>
                <p style="color: #94a3b8;">Try uploading an RFP document that contains cable specifications like:<br>
                <span style="color: #a5b4fc;">"2.5 sq mm 3 core PVC copper cable"</span> or <span style="color: #a5b4fc;">"4 x 16 sqmm XLPE armoured"</span></p>
            </div>
        `;
        return;
    }
    
    // OEM Summary Section (if available)
    let oemSummaryHtml = '';
    if (oemSummary && oemSummary.oem_rankings && oemSummary.oem_rankings.length > 0) {
        oemSummaryHtml = `
            <div class="oem-summary-section" style="margin-bottom: 24px; padding: 20px; background: #0f172a; border-radius: 16px; border: 1px solid #334155;">
                <h3 style="margin: 0 0 16px 0; color: #f1f5f9; font-size: 1.1rem;">🏆 OEM Performance Summary</h3>
                <div class="oem-ranking-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px;">
                    ${oemSummary.oem_rankings.map((oem, idx) => `
                        <div class="oem-rank-card" style="padding: 14px; background: ${idx === 0 ? 'linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 183, 0, 0.1))' : 'linear-gradient(135deg, rgba(30, 41, 59, 1), rgba(51, 65, 85, 1))'}; border-radius: 10px; border: 1px solid ${idx === 0 ? '#ffd700' : '#475569'};">
                            <div style="font-size: 1.1rem; font-weight: 700; color: ${idx === 0 ? '#ffd700' : idx === 1 ? '#c0c0c0' : '#f1f5f9'}; margin-bottom: 8px;">
                                ${idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '#' + (idx + 1)} ${oem.oem}
                            </div>
                            <div style="display: grid; gap: 4px; font-size: 0.8rem; color: #94a3b8;">
                                <div>Appearances: <strong style="color: #e2e8f0;">${oem.appearances}</strong></div>
                                <div>Avg Match: <strong style="color: #22c55e;">${oem.avg_match_score}%</strong></div>
                                ${oem.avg_price ? `<div>Avg Price: <strong style="color: #4ade80;">₹${oem.avg_price}/m</strong></div>` : ''}
                                ${oem.max_warranty ? `<div>Warranty: <strong style="color: #60a5fa;">${oem.max_warranty} yrs</strong></div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Build comparison cards
    let comparisonsHtml = '';
    
    comparisons.forEach((comp, idx) => {
        const req = comp.requirement || {};
        const matches = comp.top_matches || [];
        
        // Requirement specs tags
        const reqTags = [];
        if (req.conductor_size) reqTags.push(`<strong style="color: #818cf8;">${req.conductor_size}</strong> sq mm`);
        if (req.cores) reqTags.push(`<strong style="color: #818cf8;">${req.cores}</strong> Core`);
        if (req.voltage) reqTags.push(`<strong style="color: #818cf8;">${req.voltage}</strong>V`);
        if (req.conductor_material) reqTags.push(`<strong style="color: #818cf8;">${req.conductor_material}</strong>`);
        if (req.insulation) reqTags.push(`<strong style="color: #818cf8;">${req.insulation}</strong>`);
        if (req.armoured !== undefined) reqTags.push(req.armoured ? '🛡️ Armoured' : 'Unarmoured');
        if (req.current_rating) reqTags.push(`<strong style="color: #818cf8;">${req.current_rating}</strong> Amp`);
        
        // Build enhanced product cards
        const productCardsHtml = matches.length === 0 ? 
            `<div style="text-align: center; color: #94a3b8; padding: 40px;">❌ No matching products found</div>` :
            `<div class="match-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
                ${matches.map((m, i) => createEnhancedProductCard(m, i + 1, req, analysisOptions)).join('')}
            </div>`;
        
        // Build comparison table
        const comparisonTableHtml = matches.length > 0 ? createComparisonTable(matches, req, idx) : '';
        
        comparisonsHtml += `
            <div class="comparison-card" style="background: #0f172a; border-radius: 16px; margin-bottom: 24px; overflow: hidden; border: 1px solid #334155;">
                <div class="requirement-header" style="padding: 16px 20px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(59, 130, 246, 0.2)); border-bottom: 1px solid #334155;">
                    <h3 style="font-size: 1.1rem; color: #f1f5f9; margin: 0 0 8px 0;">📋 Requirement #${idx + 1}</h3>
                    ${req.original_text ? `<p style="margin-bottom: 10px; color: #94a3b8; font-style: italic; font-size: 0.9rem;">"${req.original_text}"</p>` : ''}
                    <div class="requirement-specs" style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${reqTags.map(tag => `<span style="padding: 4px 10px; background: #1e293b; border-radius: 4px; font-size: 0.85rem; color: #cbd5e1;">${tag}</span>`).join('')}
                    </div>
                </div>
                
                <div class="matches-container" style="padding: 20px;">
                    ${productCardsHtml}
                    ${comparisonTableHtml}
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = headerHtml + oemSummaryHtml + comparisonsHtml;
    
    // Add toggle event listeners for comparison tables
    document.querySelectorAll('.toggle-table-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const table = btn.nextElementSibling;
            table.style.display = table.style.display === 'none' ? 'table' : 'none';
            btn.textContent = table.style.display === 'none' 
                ? '📊 Show Comparison Table' 
                : '📊 Hide Comparison Table';
        });
    });
    
    // Add toggle event listeners for calculations panels
    document.querySelectorAll('.toggle-calc-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const panel = btn.nextElementSibling;
            const isHidden = panel.style.display === 'none';
            panel.style.display = isHidden ? 'block' : 'none';
            btn.textContent = isHidden ? '📉 Hide Calculations' : '📊 Show Calculations';
        });
    });
}

// Create an enhanced product card with calculations and recommendations
function createEnhancedProductCard(match, rank, requirement, analysisOptions) {
    const scoreClass = match.match_score >= 70 ? '#22c55e' : 
                      match.match_score >= 50 ? '#eab308' : '#f97316';
    
    const rankColors = {
        1: { border: '#ffd700', bg: 'linear-gradient(135deg, #ffd700, #ffb700)', color: '#1a1a1a', shadow: 'rgba(255, 215, 0, 0.3)' },
        2: { border: '#c0c0c0', bg: 'linear-gradient(135deg, #c0c0c0, #a0a0a0)', color: '#1a1a1a', shadow: 'rgba(192, 192, 192, 0.3)' },
        3: { border: '#cd7f32', bg: 'linear-gradient(135deg, #cd7f32, #a56020)', color: 'white', shadow: 'rgba(205, 127, 50, 0.3)' }
    };
    
    const rankStyle = rankColors[rank] || rankColors[3];
    
    // Build calculations panel
    let calculationsHtml = '';
    if (match.voltage_drop || match.power_capacity || match.short_circuit) {
        const vd = match.voltage_drop || {};
        const pc = match.power_capacity || {};
        const sc = match.short_circuit || {};
        
        const vdStatusColor = vd.status === 'Excellent' ? '#22c55e' : 
                             vd.status === 'Good' ? '#4ade80' : 
                             vd.status === 'Acceptable' ? '#eab308' : '#ef4444';
        
        calculationsHtml = `
            <div class="calculations-section" style="margin-top: 14px; padding-top: 14px; border-top: 1px solid #334155;">
                <button class="toggle-calc-btn" style="background: #1e293b; border: 1px solid #475569; padding: 6px 12px; border-radius: 6px; color: #94a3b8; cursor: pointer; font-size: 0.8rem; width: 100%; transition: all 0.2s;">
                    📊 Show Calculations
                </button>
                <div class="calculations-panel" style="display: none; margin-top: 10px;">
                    ${vd.drop_percent !== undefined ? `
                    <div class="calc-item" style="padding: 10px; background: #0f172a; border-radius: 8px; margin-bottom: 8px;">
                        <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 4px;">⚡ Voltage Drop (${vd.cable_length}m)</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 1.1rem; font-weight: 700; color: ${vdStatusColor};">${vd.drop_percent?.toFixed(2) || '-'}%</span>
                            <span style="font-size: 0.8rem; color: ${vdStatusColor}; padding: 2px 8px; background: ${vdStatusColor}22; border-radius: 4px;">${vd.status || '-'}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">
                            ${vd.drop_volts?.toFixed(2) || '-'}V drop | 
                            Feeder: ${vd.compliant_feeder ? '✅' : '❌'} | 
                            Branch: ${vd.compliant_branch ? '✅' : '❌'}
                        </div>
                    </div>` : ''}
                    
                    ${pc.power_kw !== undefined ? `
                    <div class="calc-item" style="padding: 10px; background: #0f172a; border-radius: 8px; margin-bottom: 8px;">
                        <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 4px;">⚡ Power Capacity</div>
                        <div style="display: flex; gap: 16px;">
                            <div>
                                <span style="font-size: 1.1rem; font-weight: 700; color: #60a5fa;">${pc.power_kw?.toFixed(1) || '-'}</span>
                                <span style="font-size: 0.8rem; color: #60a5fa;"> kW</span>
                            </div>
                            <div>
                                <span style="font-size: 1.1rem; font-weight: 700; color: #a78bfa;">${pc.power_kva?.toFixed(1) || '-'}</span>
                                <span style="font-size: 0.8rem; color: #a78bfa;"> kVA</span>
                            </div>
                        </div>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">
                            Derated Current: ${pc.current_capacity?.toFixed(1) || '-'} A
                        </div>
                    </div>` : ''}
                    
                    ${sc.withstand_1s_kA !== undefined ? `
                    <div class="calc-item" style="padding: 10px; background: #0f172a; border-radius: 8px;">
                        <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 4px;">⚡ Short Circuit Withstand</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #f97316;">${sc.withstand_1s_kA?.toFixed(2) || '-'} kA</div>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">I²t: ${sc.i2t_rating ? (sc.i2t_rating / 1000000).toFixed(2) + 'M' : '-'} A²s</div>
                    </div>` : ''}
                </div>
            </div>
        `;
    }
    
    // Build recommendations panel
    let recommendationsHtml = '';
    if (match.recommendations && match.recommendations.length > 0) {
        recommendationsHtml = `
            <div class="recommendations-section" style="margin-top: 10px; padding: 10px; background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(59, 130, 246, 0.1)); border-radius: 8px; border: 1px solid #334155;">
                <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 6px;">💡 Recommendations</div>
                <ul style="margin: 0; padding-left: 16px; font-size: 0.8rem; color: #94a3b8; line-height: 1.6;">
                    ${match.recommendations.map(rec => `<li style="margin-bottom: 2px;">${rec}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Build budget analysis panel
    let budgetHtml = '';
    if (match.budget_analysis) {
        const ba = match.budget_analysis;
        const valueColor = ba.value_rating === 'Excellent Value' ? '#22c55e' :
                          ba.value_rating === 'Good Value' ? '#4ade80' :
                          ba.value_rating === 'Fair Value' ? '#eab308' : '#818cf8';
        
        budgetHtml = `
            <div class="budget-section" style="margin-top: 10px; padding: 10px; background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.1)); border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b;">Total Cost (${ba.cable_length}m)</div>
                        <div style="font-size: 1.3rem; font-weight: 700; color: #22c55e;">₹${ba.total_cost?.toLocaleString() || '-'}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: #64748b;">Value Rating</div>
                        <div style="font-size: 0.9rem; font-weight: 600; color: ${valueColor};">${ba.value_rating || '-'}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    return `
        <div class="match-card" style="background: #1e293b; border-radius: 12px; padding: 16px; border: 2px solid ${rankStyle.border}; position: relative; box-shadow: 0 0 20px ${rankStyle.shadow};">
            <div class="match-rank" style="position: absolute; top: -12px; right: 12px; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem; background: ${rankStyle.bg}; color: ${rankStyle.color};">
                #${rank}
            </div>
            
            <div class="match-oem" style="font-size: 0.85rem; color: #818cf8; font-weight: 600; margin-bottom: 4px;">${match.oem || 'Unknown'}</div>
            <div class="match-name" style="font-size: 1rem; font-weight: 600; color: #f1f5f9; margin-bottom: 6px; line-height: 1.3; padding-right: 30px;">${match.product_name || 'Cable/Wire Product'}</div>
            <div class="match-code" style="font-size: 0.8rem; color: #64748b; margin-bottom: 12px;">${match.product_code || ''}</div>
            
            <div class="match-score" style="display: inline-block; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 1rem; margin-bottom: 14px; background: ${scoreClass}22; color: ${scoreClass}; border: 1px solid ${scoreClass};">
                ${match.match_score}% Match
            </div>
            
            <div class="match-specs" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                <div class="match-spec">
                    <span style="color: #64748b; font-size: 0.75rem; display: block;">Size</span>
                    <span style="color: #e2e8f0; font-weight: 500;">${match.conductor_size || '-'} sq mm</span>
                </div>
                <div class="match-spec">
                    <span style="color: #64748b; font-size: 0.75rem; display: block;">Cores</span>
                    <span style="color: #e2e8f0; font-weight: 500;">${match.cores || '-'}</span>
                </div>
                <div class="match-spec">
                    <span style="color: #64748b; font-size: 0.75rem; display: block;">Voltage</span>
                    <span style="color: #e2e8f0; font-weight: 500;">${match.voltage_rating || '-'}</span>
                </div>
                <div class="match-spec">
                    <span style="color: #64748b; font-size: 0.75rem; display: block;">Material</span>
                    <span style="color: #e2e8f0; font-weight: 500;">${match.conductor_material || '-'}</span>
                </div>
                <div class="match-spec">
                    <span style="color: #64748b; font-size: 0.75rem; display: block;">Insulation</span>
                    <span style="color: #e2e8f0; font-weight: 500;">${match.insulation_type || '-'}</span>
                </div>
                <div class="match-spec">
                    <span style="color: #64748b; font-size: 0.75rem; display: block;">Current</span>
                    <span style="color: #e2e8f0; font-weight: 500;">${match.current_rating || '-'} A</span>
                </div>
            </div>
            
            ${match.price_per_meter && !match.budget_analysis ? `
                <div class="match-price" style="margin-top: 14px; padding-top: 14px; border-top: 1px solid #334155; font-size: 1.2rem; font-weight: 700; color: #22c55e;">
                    ₹${parseFloat(match.price_per_meter).toFixed(2)}/m
                </div>
            ` : ''}
            
            ${budgetHtml}
            ${recommendationsHtml}
            ${calculationsHtml}
        </div>
    `;
}

// Create a product card for spec comparer (kept for compatibility)
function createProductCard(match, rank, requirement) {
    return createEnhancedProductCard(match, rank, requirement, {});
}

// Create comparison table for spec comparer
function createComparisonTable(matches, requirement, idx) {
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
    
    let rows = specs.map(spec => {
        const reqValue = requirement[spec.reqKey];
        const reqDisplay = formatSpecValue(reqValue, spec.unit, spec.key);
        
        return `
            <tr>
                <td style="padding: 10px 12px; border: 1px solid #334155; font-weight: 600; color: #e2e8f0;">${spec.label}</td>
                <td style="padding: 10px 12px; border: 1px solid #334155; color: #94a3b8; background: #1e293b;">${reqDisplay || '-'}</td>
                ${matches.map(m => {
                    const val = m[spec.key];
                    const display = formatSpecValue(val, spec.unit, spec.key);
                    const matchStyle = getMatchStyle(val, reqValue, spec.key);
                    return `<td style="padding: 10px 12px; border: 1px solid #334155; ${matchStyle}">${display || '-'}</td>`;
                }).join('')}
            </tr>
        `;
    }).join('');
    
    return `
        <div class="comparison-table-wrapper" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #334155;">
            <button class="toggle-table-btn" style="background: #1e293b; border: 1px solid #334155; padding: 10px 20px; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: 0.95rem; width: 100%; transition: all 0.2s;">
                📊 Show Comparison Table
            </button>
            <table class="comparison-table" style="margin-top: 12px; width: 100%; border-collapse: collapse; font-size: 0.85rem; display: none; background: #0f172a;">
                <thead>
                    <tr style="background: #1e293b;">
                        <th style="padding: 12px; border: 1px solid #334155; text-align: left; color: #94a3b8; font-weight: 600;">Specification</th>
                        <th style="padding: 12px; border: 1px solid #334155; text-align: left; color: #94a3b8; font-weight: 600;">RFP Required</th>
                        ${matches.map((m, i) => `<th style="padding: 12px; border: 1px solid #334155; text-align: left; color: ${i === 0 ? '#ffd700' : i === 1 ? '#c0c0c0' : '#cd7f32'}; font-weight: 600;">#${i+1} ${m.oem}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}

// Format value for spec comparison display
function formatSpecValue(value, unit, key) {
    if (value === null || value === undefined || value === '') return null;
    
    if (key === 'is_armoured' || key === 'armoured') {
        if (typeof value === 'boolean') return value ? 'Yes' : 'No';
        return parseInt(value) ? 'Yes' : 'No';
    }
    
    if (key === 'price_per_meter' && value) {
        return `₹${parseFloat(value).toFixed(2)}`;
    }
    
    if (key === 'overall_quality_score' && value) {
        return `${value}/100`;
    }
    
    if (unit && unit !== '₹' && unit !== '/100') {
        return `${value}${unit}`;
    }
    
    return value;
}

// Get match styling for table cell
function getMatchStyle(productVal, reqVal, key) {
    if (reqVal === null || reqVal === undefined) return 'color: #e2e8f0;';
    if (productVal === null || productVal === undefined) return 'background: rgba(239, 68, 68, 0.1); color: #ef4444;';
    
    const pVal = String(productVal).toLowerCase();
    const rVal = String(reqVal).toLowerCase();
    
    if (key === 'conductor_size' || key === 'cores' || key === 'current_rating') {
        const pNum = parseFloat(productVal);
        const rNum = parseFloat(reqVal);
        if (isNaN(pNum) || isNaN(rNum)) return 'background: rgba(239, 68, 68, 0.1); color: #ef4444;';
        
        if (pNum === rNum) return 'background: rgba(34, 197, 94, 0.15); color: #22c55e;';
        if (Math.abs(pNum - rNum) / rNum < 0.1) return 'background: rgba(245, 158, 11, 0.15); color: #eab308;';
        if (key === 'current_rating' && pNum >= rNum) return 'background: rgba(34, 197, 94, 0.15); color: #22c55e;';
        return 'background: rgba(239, 68, 68, 0.1); color: #ef4444;';
    }
    
    if (key === 'is_armoured' || key === 'armoured') {
        const pBool = pVal === 'yes' || pVal === '1' || pVal === 'true';
        const rBool = typeof reqVal === 'boolean' ? reqVal : rVal === 'yes' || rVal === '1' || rVal === 'true';
        return pBool === rBool ? 'background: rgba(34, 197, 94, 0.15); color: #22c55e;' : 'background: rgba(239, 68, 68, 0.1); color: #ef4444;';
    }
    
    // String comparison
    if (pVal === rVal) return 'background: rgba(34, 197, 94, 0.15); color: #22c55e;';
    if (pVal.includes(rVal) || rVal.includes(pVal)) return 'background: rgba(245, 158, 11, 0.15); color: #eab308;';
    return 'background: rgba(239, 68, 68, 0.1); color: #ef4444;';
}

// Display Hyperlink Extraction Results
function displayHyperlinkResults(data) {
    resultsContainer.innerHTML = '';
    
    const totalLinks = data.total_links || 0;
    const downloadedCount = data.downloaded_count || 0;
    const extractedCount = data.extracted_count || 0;
    const linksByType = data.links_by_document_type || {};
    const fileTypeCounts = data.file_type_counts || {};
    const allLinks = data.all_links || [];
    const extractedContent = data.extracted_content || {};
    
    // Document type icons
    const typeIcons = {
        'boq': '📋',
        'specification': '📜',
        'drawing': '📐',
        'terms': '📝',
        'annexure': '📎',
        'eligibility': '✅',
        'corrigendum': '📢',
        'sample_format': '📄',
        'document': '📄',
        'other': '📁',
        'unknown': '🔗'
    };
    
    // File type colors
    const fileTypeColors = {
        'excel': '#217346',
        'csv': '#217346',
        'pdf': '#dc2626',
        'word': '#2b579a',
        'image': '#7c3aed',
        'unknown': '#6b7280'
    };
    
    let html = `
        <div class="result-item hyperlink-results">
            <h3>🔗 Hyperlink Extraction & Content Analysis</h3>
            
            <!-- Summary Stats -->
            <div class="result-stats" style="margin-bottom: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;">
                <div class="stat-card" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 15px; border-radius: 10px; text-align: center;">
                    <div class="stat-value" style="color: white; font-size: 1.8rem; font-weight: 700;">${totalLinks}</div>
                    <div class="stat-label" style="color: rgba(255,255,255,0.8); font-size: 0.85rem;">Links Found</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #10b981, #059669); padding: 15px; border-radius: 10px; text-align: center;">
                    <div class="stat-value" style="color: white; font-size: 1.8rem; font-weight: 700;">${downloadedCount}</div>
                    <div class="stat-label" style="color: rgba(255,255,255,0.8); font-size: 0.85rem;">Downloaded</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); padding: 15px; border-radius: 10px; text-align: center;">
                    <div class="stat-value" style="color: white; font-size: 1.8rem; font-weight: 700;">${extractedCount}</div>
                    <div class="stat-label" style="color: rgba(255,255,255,0.8); font-size: 0.85rem;">Content Extracted</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #f59e0b, #d97706); padding: 15px; border-radius: 10px; text-align: center;">
                    <div class="stat-value" style="color: white; font-size: 1.8rem; font-weight: 700;">${Object.keys(fileTypeCounts).length}</div>
                    <div class="stat-label" style="color: rgba(255,255,255,0.8); font-size: 0.85rem;">File Types</div>
                </div>
            </div>
    `;
    
    // BOQ Items Extracted
    if (extractedContent.boq_items && extractedContent.boq_items.length > 0) {
        html += `
            <div class="extracted-boq" style="margin-bottom: 20px; border: 2px solid #217346; border-radius: 10px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #217346, #166534); padding: 12px 16px; color: white;">
                    <h4 style="margin: 0; display: flex; align-items: center; gap: 8px;">
                        📋 BOQ / Price Schedule Data Extracted
                        <span style="background: rgba(255,255,255,0.2); padding: 2px 10px; border-radius: 10px; font-size: 12px;">
                            ${extractedContent.boq_items.reduce((sum, boq) => sum + (boq.items?.length || 0), 0)} items from ${extractedContent.boq_items.length} file(s)
                        </span>
                    </h4>
                </div>
                <div style="padding: 16px; background: #f0fdf4;">
        `;
        
        for (const boq of extractedContent.boq_items) {
            // Get columns - either from response or default
            const columns = boq.columns || ['Sr No', 'Description', 'Specification', 'Quantity', 'Unit'];
            
            html += `
                <div style="margin-bottom: 16px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="background: #ecfdf5; padding: 10px 14px; border-bottom: 1px solid #d1fae5;">
                        <strong>📄 Source:</strong> ${escapeHtml(boq.source || 'Unknown')}
                        ${boq.columns ? `<span style="margin-left: 10px; color: #059669; font-size: 11px;">(${boq.columns.length} columns)</span>` : ''}
                    </div>
                    <div style="max-height: 400px; overflow-y: auto; overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; min-width: 600px;">
                            <thead>
                                <tr style="background: #f8fafc; position: sticky; top: 0;">
            `;
            
            // Dynamic headers from columns
            for (const col of columns.slice(0, 8)) {
                html += `<th style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: left; white-space: nowrap;">${escapeHtml(col)}</th>`;
            }
            html += `</tr></thead><tbody>`;
            
            for (const item of (boq.items || []).slice(0, 50)) {
                html += `<tr style="border-bottom: 1px solid #f1f5f9;">`;
                
                // Map item fields to display based on available data
                const itemValues = [
                    item.sr_no || item['Item Number'] || '-',
                    item.description || item['Item Title'] || item['Item Description'] || '-',
                    item.specification || item['Specification'] || '-',
                    item.quantity || item['Item Quantity'] || '-',
                    item.unit || item['Unit of Measure'] || '-'
                ];
                
                // If we have column names, try to match them
                if (boq.columns) {
                    for (let i = 0; i < Math.min(boq.columns.length, 8); i++) {
                        const colName = boq.columns[i];
                        let val = item[colName] || itemValues[i] || '-';
                        if (typeof val === 'string' && val.length > 80) {
                            val = val.substring(0, 80) + '...';
                        }
                        html += `<td style="padding: 8px; max-width: 200px; word-wrap: break-word;">${escapeHtml(String(val))}</td>`;
                    }
                } else {
                    for (const val of itemValues) {
                        html += `<td style="padding: 8px; max-width: 200px; word-wrap: break-word;">${escapeHtml(String(val).substring(0, 80))}</td>`;
                    }
                }
                html += `</tr>`;
            }
            
            if ((boq.items?.length || 0) > 50) {
                html += `<tr><td colspan="${Math.min(columns.length, 8)}" style="padding: 10px; text-align: center; color: #64748b;">... and ${boq.items.length - 50} more items</td></tr>`;
            }
            
            html += `</tbody></table></div></div>`;
        }
        
        html += `</div></div>`;
    }
    
    // Specifications Extracted
    if (extractedContent.specifications && extractedContent.specifications.length > 0) {
        html += `
            <div class="extracted-specs" style="margin-bottom: 20px; border: 2px solid #7c3aed; border-radius: 10px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #7c3aed, #6d28d9); padding: 12px 16px; color: white;">
                    <h4 style="margin: 0; display: flex; align-items: center; gap: 8px;">
                        📜 Specifications Extracted
                        <span style="background: rgba(255,255,255,0.2); padding: 2px 10px; border-radius: 10px; font-size: 12px;">
                            ${extractedContent.specifications.length} documents
                        </span>
                    </h4>
                </div>
                <div style="padding: 16px; background: #faf5ff;">
        `;
        
        for (const spec of extractedContent.specifications) {
            html += `
                <div style="margin-bottom: 12px; background: white; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="font-weight: 600; color: #7c3aed; margin-bottom: 8px;">📄 ${escapeHtml(spec.source || 'Unknown Document')}</div>
            `;
            
            if (spec.data) {
                if (spec.data.specifications?.length > 0) {
                    html += `<div style="margin-bottom: 8px;"><strong>Specifications:</strong> ${spec.data.specifications.slice(0, 5).map(s => escapeHtml(s)).join(', ')}</div>`;
                }
                if (spec.data.standards?.length > 0) {
                    html += `<div style="margin-bottom: 8px;"><strong>Standards:</strong> ${spec.data.standards.map(s => `<span style="background: #e0e7ff; padding: 2px 8px; border-radius: 4px; margin-right: 4px;">${escapeHtml(s)}</span>`).join('')}</div>`;
                }
                if (spec.data.make_model?.length > 0) {
                    html += `<div style="margin-bottom: 8px;"><strong>Make/Model:</strong> ${spec.data.make_model.slice(0, 5).map(s => escapeHtml(s)).join(', ')}</div>`;
                }
                if (spec.data.raw_text_excerpt) {
                    html += `<details style="margin-top: 8px;"><summary style="cursor: pointer; color: #7c3aed;">View Raw Text Excerpt</summary><pre style="margin-top: 8px; padding: 10px; background: #f8fafc; border-radius: 4px; font-size: 11px; max-height: 200px; overflow-y: auto; white-space: pre-wrap;">${escapeHtml(spec.data.raw_text_excerpt)}</pre></details>`;
                }
            }
            
            html += `</div>`;
        }
        
        html += `</div></div>`;
    }
    
    // Other Documents with Extracted Text
    if (extractedContent.other_documents && extractedContent.other_documents.length > 0) {
        html += `
            <div class="extracted-other" style="margin-bottom: 20px; border: 2px solid #3b82f6; border-radius: 10px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #3b82f6, #2563eb); padding: 12px 16px; color: white;">
                    <h4 style="margin: 0;">📄 Other Document Content Extracted</h4>
                </div>
                <div style="padding: 16px; background: #eff6ff;">
        `;
        
        for (const doc of extractedContent.other_documents) {
            html += `
                <div style="margin-bottom: 12px; background: white; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="font-weight: 600; color: #3b82f6; margin-bottom: 8px;">📄 ${escapeHtml(doc.source || 'Document')} <span style="font-size: 11px; color: #64748b;">(${escapeHtml(doc.type || 'unknown')})</span></div>
                    ${doc.text_preview ? `<details><summary style="cursor: pointer; color: #3b82f6;">View Extracted Text</summary><pre style="margin-top: 8px; padding: 10px; background: #f8fafc; border-radius: 4px; font-size: 11px; max-height: 300px; overflow-y: auto; white-space: pre-wrap;">${escapeHtml(doc.text_preview)}</pre></details>` : '<p style="color: #64748b; font-style: italic;">No text content extracted</p>'}
                </div>
            `;
        }
        
        html += `</div></div>`;
    }
    
    // File Type Breakdown
    if (Object.keys(fileTypeCounts).length > 0) {
        html += `
            <div class="file-type-breakdown" style="margin-bottom: 20px; padding: 15px; background: #f8fafc; border-radius: 8px;">
                <h4 style="margin-bottom: 10px; color: #1e293b;">📁 File Types Found</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
        `;
        
        for (const [fileType, count] of Object.entries(fileTypeCounts)) {
            const color = fileTypeColors[fileType] || fileTypeColors.unknown;
            html += `
                <span style="display: inline-flex; align-items: center; padding: 6px 12px; background: ${color}15; border: 1px solid ${color}40; border-radius: 20px; font-size: 13px;">
                    <span style="color: ${color}; font-weight: 600;">${fileType.toUpperCase()}</span>
                    <span style="margin-left: 6px; background: ${color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">${count}</span>
                </span>
            `;
        }
        
        html += `</div></div>`;
    }
    
    // All Links Table
    if (Object.keys(linksByType).length > 0) {
        html += `<div class="links-by-type"><h4 style="margin-bottom: 12px; color: #1e293b;">🔗 All Hyperlinks Found</h4>`;
        
        for (const [docType, links] of Object.entries(linksByType)) {
            const icon = typeIcons[docType] || typeIcons.unknown;
            const typeName = docType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            html += `
                <div class="link-type-section" style="margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
                    <div class="link-type-header" style="background: linear-gradient(135deg, #f1f5f9, #e2e8f0); padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="toggleLinkSection(this)">
                        <span style="font-weight: 600; color: #1e293b;">
                            ${icon} ${typeName}
                        </span>
                        <span style="background: #3b82f6; color: white; padding: 4px 10px; border-radius: 15px; font-size: 12px;">
                            ${links.length} link${links.length !== 1 ? 's' : ''}
                        </span>
                    </div>
                    <div class="link-type-content" style="padding: 0; max-height: 400px; overflow-y: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                            <thead>
                                <tr style="background: #f8fafc; position: sticky; top: 0;">
                                    <th style="padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0;">Page</th>
                                    <th style="padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0;">Link Name</th>
                                    <th style="padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0;">Type</th>
                                    <th style="padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0;">Status</th>
                                    <th style="padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0;">URL</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            for (const link of links) {
                const fileColor = fileTypeColors[link.file_type] || fileTypeColors.unknown;
                const truncatedUrl = link.url.length > 50 ? link.url.substring(0, 50) + '...' : link.url;
                const linkName = link.name || link.link_text || 'Unnamed Link';
                const status = link.is_downloaded ? 
                    (link.extracted_data ? '✅ Extracted' : '⬇️ Downloaded') : 
                    (link.error ? '❌ Failed' : '⏳ Not downloaded');
                const statusColor = link.is_downloaded ? '#10b981' : (link.error ? '#ef4444' : '#f59e0b');
                
                html += `
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 12px; color: #64748b;">${link.page_number}</td>
                        <td style="padding: 10px 12px; font-weight: 500; color: #1e293b; max-width: 200px; word-break: break-word;">${escapeHtml(linkName)}</td>
                        <td style="padding: 10px 12px;">
                            <span style="display: inline-block; padding: 3px 8px; background: ${fileColor}15; color: ${fileColor}; border-radius: 4px; font-size: 11px; font-weight: 600;">
                                ${(link.file_type || 'unknown').toUpperCase()}
                            </span>
                        </td>
                        <td style="padding: 10px 12px; color: ${statusColor}; font-size: 12px;">${status}</td>
                        <td style="padding: 10px 12px;">
                            <a href="${escapeHtml(link.url)}" target="_blank" rel="noopener" style="color: #3b82f6; text-decoration: none; word-break: break-all;" title="${escapeHtml(link.url)}">
                                ${escapeHtml(truncatedUrl)}
                            </a>
                        </td>
                    </tr>
                `;
            }
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
    }
    
    // No links found message
    if (totalLinks === 0) {
        html += `
            <div style="text-align: center; padding: 40px; color: #64748b;">
                <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                <p style="font-size: 16px;">No hyperlinks found in this PDF</p>
                <p style="font-size: 13px; margin-top: 8px;">The document may not contain any clickable links or external file references.</p>
            </div>
        `;
    }
    
    html += `</div>`;
    
    resultsContainer.innerHTML = html;
}

// Helper function to toggle link sections
function toggleLinkSection(header) {
    const content = header.nextElementSibling;
    if (content.style.maxHeight === '0px' || content.style.display === 'none') {
        content.style.maxHeight = '400px';
        content.style.display = 'block';
    } else {
        content.style.maxHeight = '0px';
        content.style.display = 'none';
    }
}

// HTML escape helper
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function cancelOperation() {
    if (requestAbortController) {
        requestAbortController.abort();
        isProcessing = false;
        hideLoading();
        showError('Operation cancelled by user');
    }
}

// Display Results
function displayResults(data, type) {
    resultsContainer.innerHTML = '';

    // Show accuracy metrics if available (NEW)
    if (data.report) {
        displayAccuracyMetrics(data);
    }

    if (type === 'text') {
        displayTextResults(data);
    } else if (type === 'analysis') {
        displayAnalysisResults(data);
    } else if (type === 'sections') {
        displaySectionsResults(data);
    }
}

function displayMultilingualResults(data) {
    resultsContainer.innerHTML = '';
    
    // Show accuracy metrics if available (NEW)
    if (data.report) {
        displayAccuracyMetrics(data);
    }

    const languageDetection = data.language_detection || {};
    const extractedContent = data.extracted_content || {};
    const summary = data.language_summary || {};
    
    let html = `
        <div class="result-item">
            <h3>🌐 Multilingual RFP Analysis & Extraction Results (v3.2)</h3>
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-size: 14px;">
                <strong>✓ Unicode Normalized (NFKC):</strong> Hindi/Marathi text cleaned and standardized for accurate analysis | <strong>1,500+ RFP Terms:</strong> Enhanced detection across 30+ categories
            </div>
            <div class="result-stats">
                <div class="stat-card">
                    <div class="stat-value">${(data.metadata?.total_words || 0).toLocaleString()}</div>
                    <div class="stat-label">Total Words</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${(data.metadata?.total_text_length || 0).toLocaleString()}</div>
                    <div class="stat-label">Total Characters</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${(languageDetection.detected_languages || []).length}</div>
                    <div class="stat-label">Languages Detected</div>
                </div>
            </div>
    `;
    
    // Language detection info
    if (languageDetection.detected_languages && languageDetection.detected_languages.length > 0) {
        html += `<p style="margin: 15px 0; color: #10b981;"><strong>✓ Detected Languages:</strong> ${languageDetection.detected_languages.join(', ').toUpperCase()}</p>`;
    }
    
    // Language tabs with full extraction
    html += '<div class="language-tabs">';
    ['english', 'hindi', 'marathi'].forEach((lang, index) => {
        const langContent = extractedContent[lang] || {};
        const langSummary = summary.languages_analysis?.[lang] || {};
        const langLabel = lang === 'english' ? '🇬🇧 English' : lang === 'hindi' ? '🇮🇳 Hindi (हिंदी)' : '🇮🇳 Marathi (मराठी)';
        
        let detectionStatus = '';
        if (langContent.detected) {
            detectionStatus = '<span style="color: #10b981; font-weight: bold;">✓ Detected</span>';
        } else {
            detectionStatus = '<span style="color: #ef4444;">✗ Not detected</span>';
        }
        
        html += `
            <div class="language-tab">
                <h4>${langLabel} <small style="font-size: 12px; margin-left: 10px;">${detectionStatus}</small></h4>
                
                <div class="language-stats">
                    <div class="stat-card">
                        <div class="stat-value">${langContent.text_length || 0}</div>
                        <div class="stat-label">Extracted Chars</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${langContent.term_analysis?.total_terms_found || 0}</div>
                        <div class="stat-label">Terms Found</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${langSummary.categories_with_matches || 0}</div>
                        <div class="stat-label">Categories</div>
                    </div>
                </div>
                
                <div style="margin-top: 15px;">
                    <h5>📄 Extracted Text Preview:</h5>
                    <div class="result-text" id="text-preview-${lang}" style="max-height: 200px; overflow-y: auto; background: #f3f4f6; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    </div>
                </div>
        `;
        
        // Show top categories with matches
        if (langContent.term_analysis?.categories) {
            html += '<div style="margin-top: 15px;"><h5>📊 Top Matching Categories:</h5><div class="category-breakdown">';
            Object.entries(langContent.term_analysis.categories)
                .filter(([_, stats]) => stats.has_matches)
                .slice(0, 5)
                .forEach(([category, stats]) => {
                    html += `
                        <div class="category-item-small">
                            <span>${category.replace(/_/g, ' ')}</span>
                            <span class="category-count">${stats.occurrences_found} found</span>
                        </div>
                    `;
                });
            html += '</div></div>';
        }
        
        html += '</div>';
    });
    
    html += `
            </div>
            <p style="margin-top: 20px; color: #10b981;">
                <strong>✓ Full multilingual extraction and analysis complete!</strong>
            </p>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
    
    // Set text previews using textContent to preserve Unicode/Hindi/Marathi
    ['english', 'hindi', 'marathi'].forEach(lang => {
        const previewDiv = document.getElementById(`text-preview-${lang}`);
        if (previewDiv) {
            const langContent = extractedContent[lang] || {};
            previewDiv.textContent = langContent.text_preview || 'No content extracted for this language';
        }
    });
}

function displayTextResults(data) {
    const charCount = data.full_text_length || data.data?.length || 0;
    const wordCount = data.words || Math.round(charCount / 5);
    
    const html = `
        <div class="result-item" style="background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="color: #1f2937; margin-bottom: 20px; font-size: 1.5rem;">📝 Text Extraction Results</h3>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 2rem; font-weight: 700;">${charCount.toLocaleString()}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">Total Characters</div>
                </div>
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 2rem; font-weight: 700;">${wordCount.toLocaleString()}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">Words</div>
                </div>
            </div>
            
            <h4 style="color: #374151; margin-bottom: 12px;">📄 Preview (First 2000 characters):</h4>
            <div id="textPreview" style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; max-height: 400px; overflow-y: auto; font-family: 'Noto Sans', monospace; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;"></div>
            
            <p style="margin-top: 16px; color: #10b981; font-weight: 500;">
                ✓ Extraction complete - Download full text for complete document
            </p>
        </div>
    `;
    resultsContainer.innerHTML = html;
    
    // Set the text preview using textContent to preserve Unicode/Hindi
    const previewDiv = document.getElementById('textPreview');
    if (previewDiv) {
        previewDiv.textContent = (data.data || '').substring(0, 2000);
    }
}

function displayAnalysisResults(data) {
    // Build efficient term statistics
    const termStats = data.term_statistics || {};
    const termStatsHtml = buildTermStatsHtml(termStats);
    
    const stats = {
        words: (data.total_words || 0).toLocaleString(),
        chars: (data.total_characters || 0).toLocaleString(),
        sections: data.sections_found || 0,
        terms: data.rfp_terms_found || 0
    };

    const html = `
        <div class="result-item" style="background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="color: #1f2937; margin-bottom: 20px; font-size: 1.5rem;">📊 RFP Analysis Results</h3>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 18px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: 700;">${stats.words}</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Words</div>
                </div>
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 18px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: 700;">${stats.chars}</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Characters</div>
                </div>
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 18px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: 700;">${stats.sections}</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Sections</div>
                </div>
                <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 18px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: 700;">${stats.terms}</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">RFP Terms</div>
                </div>
            </div>

            <h4 style="color: #374151; margin-bottom: 16px; font-size: 1.1rem;">📈 Term Occurrences by Category:</h4>
            <div style="background: #f9fafb; border-radius: 8px; padding: 16px;">
                ${termStatsHtml}
            </div>

            <p style="margin-top: 20px; color: #10b981; font-weight: 500;">
                ✓ Analysis complete - Download report for full details
            </p>
        </div>
    `;
    resultsContainer.innerHTML = html;
}

function buildTermStatsHtml(termStats) {
    // Filter and sort categories by occurrence count
    const sortedCategories = Object.entries(termStats)
        .filter(([key, stats]) => key !== 'total_rfp_terms_found' && (stats.total_occurrences || 0) > 0)
        .sort((a, b) => (b[1].total_occurrences || 0) - (a[1].total_occurrences || 0));
    
    if (sortedCategories.length === 0) {
        return '<p style="color: #6b7280; text-align: center;">No RFP terms found in this document</p>';
    }
    
    return '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px;">' +
        sortedCategories.map(([category, stats]) => {
            const count = stats.total_occurrences || 0;
            const bgColor = count > 10 ? '#dcfce7' : count > 5 ? '#fef3c7' : '#f3f4f6';
            const borderColor = count > 10 ? '#10b981' : count > 5 ? '#f59e0b' : '#d1d5db';
            return `
                <div style="background: ${bgColor}; border: 2px solid ${borderColor}; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">${count.toLocaleString()}</div>
                    <div style="font-size: 0.8rem; color: #4b5563; text-transform: capitalize;">${category.replace(/_/g, ' ')}</div>
                </div>
            `;
        }).join('') +
        '</div>';
}

function displaySectionsResults(data) {
    let sectionsHtml = '';
    const sectionColors = ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
    let colorIndex = 0;
    
    for (const [section, content] of Object.entries(data.sections || {})) {
        const color = sectionColors[colorIndex % sectionColors.length];
        sectionsHtml += `
            <div style="background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 16px; border-left: 4px solid ${color}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h4 style="color: ${color}; margin-bottom: 12px; font-size: 1.1rem; text-transform: capitalize;">${section.replace(/_/g, ' ')}</h4>
                <div style="background: #f9fafb; padding: 12px; border-radius: 6px; font-size: 14px; line-height: 1.6; max-height: 200px; overflow-y: auto; white-space: pre-wrap;">${escapeHtml(content || 'No content')}</div>
            </div>
        `;
        colorIndex++;
    }

    const html = `
        <div class="result-item" style="background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="color: #1f2937; margin-bottom: 20px; font-size: 1.5rem;">📑 RFP Sections Extracted</h3>
            
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 16px; border-radius: 10px; margin-bottom: 24px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 700;">${data.total_sections || 0}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">Sections Found</div>
            </div>
            
            ${sectionsHtml || '<p style="color: #6b7280; text-align: center;">No sections detected in this document</p>'}
            
            <p style="margin-top: 20px; color: #10b981; font-weight: 500;">
                ✓ Section extraction complete
            </p>
        </div>
    `;
    resultsContainer.innerHTML = html;
}

// Download Handlers (Optimized with validation)
function handleDownloadFull() {
    if (!lastExtractedFilename) {
        showError('No extraction results. Please extract a PDF first.');
        return;
    }
    
    if (isProcessing) {
        showError('Processing in progress. Please wait.');
        return;
    }

    performDownloadFile('full');
}

function handleDownloadReport() {
    if (!lastExtractedFilename) {
        showError('No extraction results. Please extract a PDF first.');
        return;
    }
    
    if (isProcessing) {
        showError('Processing in progress. Please wait.');
        return;
    }

    performDownloadFile('report');
}

function performDownloadFile(format) {
    try {
        const downloadUrl = `/api/download?filename=${encodeURIComponent(lastExtractedFilename)}&format=${format}`;
        
        // Create and trigger download link
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.setAttribute('download', '');
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        
        // Cleanup DOM node
        setTimeout(() => document.body.removeChild(link), 100);
        
        showSuccess(`Downloaded ${format} results`);
    } catch (error) {
        showError(`Download failed: ${error.message}`);
    }
}

function downloadFile(filename) {
    const link = document.createElement('a');
    link.href = `/api/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// UI Helpers (Optimized for 100k database)
function showLoading(message = '⏳ Processing...') {
    loadingIndicator.style.display = 'block';
    const existingMsg = loadingIndicator.querySelector('p');
    if (existingMsg) {
        existingMsg.textContent = message;
    } else {
        const msg = document.createElement('p');
        msg.textContent = message;
        msg.style.cssText = 'margin: 10px 0; color: #666;';
        loadingIndicator.appendChild(msg);
    }
    resultsContainer.innerHTML = '';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Animate loading indicator
    if (!loadingIndicator.classList.contains('loading-animated')) {
        loadingIndicator.classList.add('loading-animated');
    }
}

function updateLoadingMessage(message) {
    const msg = loadingIndicator.querySelector('p');
    if (msg) msg.textContent = message;
}

function hideLoading() {
    loadingIndicator.style.display = 'none';
    if (loadingIndicator.classList.contains('loading-animated')) {
        loadingIndicator.classList.remove('loading-animated');
    }
}

function showError(message) {
    errorMessage.textContent = message.startsWith('❌') ? message : '❌ ' + message;
    errorMessage.style.display = 'block';
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showSuccess(message) {
    const msg = document.createElement('div');
    msg.className = 'success-message';
    msg.textContent = message.startsWith('✓') ? message : '✓ ' + message;
    msg.style.cssText = `
        background: #dcfce7;
        color: #166534;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #10b981;
        animation: slideIn 0.3s ease-out;
    `;
    resultsContainer.insertBefore(msg, resultsContainer.firstChild);
    
    // Auto-dismiss success message after 5 seconds
    setTimeout(() => msg.remove?.(), 5000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load Database Statistics (Lightweight - no full DB load)
function loadDatabaseStatsLight() {
    // Use AbortController with timeout to prevent hanging
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    fetch(`${CONFIG.API_BASE}/terms-database/stats`, { signal: controller.signal })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) throw new Error('Stats unavailable');
            return response.json();
        })
        .then(data => {
            databaseStats = data;
            console.log('📊 Database Stats loaded:', data.database?.total_terms, 'terms');
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.warn('Stats load skipped:', error.message);
        });
}

// Load Terms Categories (Optimized with caching)
function loadTermsCategories() {
    const now = Date.now();
    
    // Return cached data if available and not expired
    if (termsCache && (now - termsCacheTime) < TERMS_CACHE_TTL) {
        renderTermsCategories(termsCache);
        return;
    }
    
    fetch(`${CONFIG.API_BASE}/terms-database`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to load terms');
            return response.json();
        })
        .then(data => {
            // Cache the result
            termsCache = data;
            termsCacheTime = now;
            renderTermsCategories(data);
        })
        .catch(error => {
            console.warn('Error loading terms categories:', error);
            // Don't crash if this fails - it's optional
        });
}

function renderTermsCategories(data) {
    const categoryHtml = data.categories && data.categories.list
        ? data.categories.list.map(cat => `
            <div class="category-item">
                <span>${cat.replace(/_/g, ' ')}</span>
            </div>
        `).join('')
        : '';

    const totalTerms = data.database_info?.total_terms || 0;
    const totalCategories = data.categories?.count || 0;
    const cacheStatus = databaseStats?.optimization?.database_caching === 'Enabled (pickle format)' 
        ? '⚡ Cached' 
        : '📦 Database';
    
    const totalHtml = `
        <div class="category-item" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: 2px solid #667eea; margin-top: 10px; font-weight: 600;">
            <span>100k+ RFP Terms ${cacheStatus}</span>
            <span class="category-count" style="color: #fff; font-weight: 700;">${totalTerms.toLocaleString()} terms</span>
        </div>
        <div class="category-item" style="background: #f0fdf4; border: 1px solid #86efac; font-size: 0.9em;">
            <span>Categories: ${totalCategories} | Languages: 3 (EN/HI/MR)</span>
        </div>
    `;
    
    if (termsCategories) {
        termsCategories.innerHTML = categoryHtml + totalHtml;
    }
}

// Display Accuracy Metrics (NEW - 99% Accuracy Feature)
function displayAccuracyMetrics(data) {
    const accuracyMetrics = document.getElementById('accuracyMetrics');
    const accuracyScore = document.getElementById('accuracyScore');
    const languagesDetected = document.getElementById('languagesDetected');
    const diacriticsCount = document.getElementById('diacriticsCount');
    const extractionMethod = document.getElementById('extractionMethod');

    if (accuracyMetrics && data.report) {
        // Display accuracy percentage
        if (accuracyScore && data.report.accuracy_percentage !== undefined) {
            const accuracy = Math.round(data.report.accuracy_percentage * 10) / 10;
            const accuracyColor = accuracy >= 98 ? '#10b981' : accuracy >= 95 ? '#f59e0b' : '#ef4444';
            accuracyScore.innerHTML = `<span style="color: ${accuracyColor};">${accuracy}%</span>`;
        }

        // Display languages detected
        if (languagesDetected && data.report.languages_detected) {
            const languages = Array.isArray(data.report.languages_detected) 
                ? data.report.languages_detected.join(', ')
                : data.report.languages_detected;
            languagesDetected.textContent = languages || 'Unknown';
        }

        // Display diacritics count
        if (diacriticsCount && data.report.diacritics_preserved !== undefined) {
            const diacriticsStatus = data.report.diacritics_preserved ? '✓ YES' : '✗ NO';
            diacriticsCount.innerHTML = `<span style="color: #10b981; font-weight: bold;">${diacriticsStatus}</span>`;
        }

        // Display extraction method
        if (extractionMethod && data.report.extraction_stats) {
            const method = data.report.extraction_stats.extraction_method || 'Standard';
            extractionMethod.textContent = method;
        }

        // Show metrics section
        accuracyMetrics.style.display = 'block';
    }
}

// Enhanced displayTextResults with accuracy metrics
function displayTextResultsWithAccuracy(data) {
    // Show accuracy metrics first
    displayAccuracyMetrics(data);
    
    // Then display regular text results
    displayTextResults(data);
}

// Initialize terms categories on page load
function initializeTermsDisplay() {
    const termsCategories = document.getElementById('termsCategories');
    if (termsCategories) {
        loadTermsCategories();
    }
}
