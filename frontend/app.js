/**
 * WillGPT Search Frontend
 *
 * Handles search requests, filter management, and result rendering
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const searchModeFilter = document.getElementById('searchModeFilter');
const platformFilter = document.getElementById('platformFilter');
const limitFilter = document.getElementById('limitFilter');
const interpretationsFilter = document.getElementById('interpretationsFilter');
const resultsContainer = document.getElementById('results');
const statsContainer = document.getElementById('statsContainer');
const queryText = document.getElementById('queryText');
const resultsCount = document.getElementById('resultsCount');
const executionTime = document.getElementById('executionTime');

// Advanced filter elements
const orderByGroup = document.getElementById('orderByGroup');
const orderDirectionGroup = document.getElementById('orderDirectionGroup');
const orderByField = document.getElementById('orderByField');
const orderDirection = document.getElementById('orderDirection');

const groupByGroup = document.getElementById('groupByGroup');
const groupSizeGroup = document.getElementById('groupSizeGroup');
const groupByField = document.getElementById('groupByField');
const groupSize = document.getElementById('groupSize');

const mmrDiversityGroup = document.getElementById('mmrDiversityGroup');
const mmrDiversity = document.getElementById('mmrDiversity');
const mmrDiversityValue = document.getElementById('mmrDiversityValue');

const positiveIdsGroup = document.getElementById('positiveIdsGroup');
const negativeIdsGroup = document.getElementById('negativeIdsGroup');
const positiveIds = document.getElementById('positiveIds');
const negativeIds = document.getElementById('negativeIds');
const recommendHelp = document.getElementById('recommendHelp');

// State
let isSearching = false;

/**
 * Initialize event listeners
 */
function init() {
    searchButton.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // Search mode changes
    searchModeFilter.addEventListener('change', updateAdvancedFilters);

    // MMR diversity slider
    mmrDiversity.addEventListener('input', (e) => {
        mmrDiversityValue.textContent = e.target.value;
    });

    // Initialize filter visibility
    updateAdvancedFilters();

    // Auto-focus search input
    searchInput.focus();
}

/**
 * Show/hide advanced filters based on search mode
 */
function updateAdvancedFilters() {
    const mode = searchModeFilter.value;

    // Hide all advanced filters first
    orderByGroup.style.display = 'none';
    orderDirectionGroup.style.display = 'none';
    groupByGroup.style.display = 'none';
    groupSizeGroup.style.display = 'none';
    mmrDiversityGroup.style.display = 'none';
    positiveIdsGroup.style.display = 'none';
    negativeIdsGroup.style.display = 'none';
    recommendHelp.style.display = 'none';

    // Show relevant filters based on mode
    if (mode === 'order_by') {
        orderByGroup.style.display = 'flex';
        orderDirectionGroup.style.display = 'flex';
    } else if (mode === 'groups') {
        groupByGroup.style.display = 'flex';
        groupSizeGroup.style.display = 'flex';
    } else if (mode === 'mmr') {
        mmrDiversityGroup.style.display = 'flex';
    } else if (mode === 'recommend') {
        positiveIdsGroup.style.display = 'flex';
        negativeIdsGroup.style.display = 'flex';
        recommendHelp.style.display = 'block';
    }
}

/**
 * Handle search execution
 */
async function handleSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        showError('Please enter a search query');
        return;
    }

    if (isSearching) {
        return;
    }

    isSearching = true;
    searchButton.disabled = true;
    searchButton.textContent = 'Searching...';

    showLoading();

    try {
        const results = await executeSearch(query);
        displayResults(results);
        updateStats(query, results);
    } catch (error) {
        showError(`Search failed: ${error.message}`);
    } finally {
        isSearching = false;
        searchButton.disabled = false;
        searchButton.textContent = 'Search';
    }
}

/**
 * Execute search API call
 */
async function executeSearch(query) {
    const params = new URLSearchParams({
        q: query,
        limit: limitFilter.value,
        search_mode: searchModeFilter.value,
    });

    const platform = platformFilter.value;
    if (platform) {
        params.append('platform', platform);
    }

    if (interpretationsFilter.checked) {
        params.append('interpretations', 'true');
    }

    // Add mode-specific parameters
    const mode = searchModeFilter.value;

    if (mode === 'order_by') {
        params.append('order_by_field', orderByField.value);
        params.append('order_direction', orderDirection.value);
    } else if (mode === 'groups') {
        params.append('group_by', groupByField.value);
        params.append('group_size', groupSize.value);
    } else if (mode === 'mmr') {
        params.append('mmr_diversity', mmrDiversity.value);
    } else if (mode === 'recommend') {
        const posIds = positiveIds.value.trim();
        if (posIds) {
            params.append('positive_ids', posIds);
        }
        const negIds = negativeIds.value.trim();
        if (negIds) {
            params.append('negative_ids', negIds);
        }
    }

    const response = await fetch(`${API_BASE_URL}/api/search?${params}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Search request failed');
    }

    return await response.json();
}

/**
 * Display search results
 */
function displayResults(data) {
    // Check if this is grouped results
    if (data.groups) {
        displayGroupedResults(data);
        return;
    }

    // Regular results
    if (!data.results || data.results.length === 0) {
        showEmptyState('No results found. Try different keywords or adjust filters.');
        return;
    }

    resultsContainer.innerHTML = '';

    data.results.forEach(result => {
        const card = createResultCard(result);
        resultsContainer.appendChild(card);
    });
}

/**
 * Display grouped search results
 */
function displayGroupedResults(data) {
    if (!data.groups || data.groups.length === 0) {
        showEmptyState('No groups found. Try different keywords or adjust filters.');
        return;
    }

    resultsContainer.innerHTML = '';

    data.groups.forEach(group => {
        // Create group header
        const groupHeader = document.createElement('div');
        groupHeader.style.cssText = 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 25px; border-radius: 12px; margin-bottom: 10px; font-weight: 600; font-size: 18px; text-transform: capitalize;';
        groupHeader.textContent = `${group.group_key} (${group.hits.length} results)`;
        resultsContainer.appendChild(groupHeader);

        // Create results for this group
        group.hits.forEach(result => {
            const card = createResultCard(result);
            card.style.marginLeft = '20px';
            resultsContainer.appendChild(card);
        });

        // Add spacing between groups
        const spacer = document.createElement('div');
        spacer.style.height = '30px';
        resultsContainer.appendChild(spacer);
    });
}

/**
 * Create a result card element
 */
function createResultCard(result) {
    const card = document.createElement('div');
    card.className = 'result-card';

    // Header with score
    const header = document.createElement('div');
    header.className = 'result-header';

    const title = document.createElement('h3');
    title.textContent = result.conversation_title;

    const score = document.createElement('div');
    score.className = 'result-score';
    score.textContent = `Score: ${result.score.toFixed(3)}`;

    header.appendChild(title);
    header.appendChild(score);
    card.appendChild(header);

    // Metadata
    const meta = document.createElement('div');
    meta.className = 'result-meta';

    const platformBadge = document.createElement('span');
    platformBadge.className = `platform-badge platform-${result.platform}`;
    platformBadge.textContent = result.platform;
    meta.appendChild(platformBadge);

    if (result.timestamp) {
        const date = new Date(result.timestamp);
        const dateSpan = document.createElement('span');
        dateSpan.className = 'meta-item';
        dateSpan.textContent = `📅 ${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
        meta.appendChild(dateSpan);
    }

    if (result.assistant_model) {
        const modelSpan = document.createElement('span');
        modelSpan.className = 'meta-item';
        modelSpan.textContent = `🤖 ${result.assistant_model}`;
        meta.appendChild(modelSpan);
    }

    const turnSpan = document.createElement('span');
    turnSpan.className = 'meta-item';
    turnSpan.textContent = `Turn ${result.turn_number}`;
    meta.appendChild(turnSpan);

    card.appendChild(meta);

    // User message
    if (result.user_message) {
        const userSection = document.createElement('div');
        userSection.className = 'message-section';

        const userLabel = document.createElement('div');
        userLabel.className = 'message-label';
        userLabel.textContent = '👤 User';

        const userContent = document.createElement('div');
        userContent.className = 'message-content';
        userContent.textContent = truncateText(result.user_message, 500);

        userSection.appendChild(userLabel);
        userSection.appendChild(userContent);
        card.appendChild(userSection);
    }

    // Assistant message
    if (result.assistant_message) {
        const assistantSection = document.createElement('div');
        assistantSection.className = 'message-section';

        const assistantLabel = document.createElement('div');
        assistantLabel.className = 'message-label';
        assistantLabel.textContent = '🤖 Assistant';

        const assistantContent = document.createElement('div');
        assistantContent.className = 'message-content';
        assistantContent.textContent = truncateText(result.assistant_message, 500);

        assistantSection.appendChild(assistantLabel);
        assistantSection.appendChild(assistantContent);
        card.appendChild(assistantSection);
    }

    // AI Interpretations
    if (result.has_interpretations && (result.about_user || result.about_model)) {
        const interpretation = document.createElement('div');
        interpretation.className = 'interpretation';

        const interpLabel = document.createElement('div');
        interpLabel.className = 'interpretation-label';
        interpLabel.textContent = '🧠 AI Interpretations';
        interpretation.appendChild(interpLabel);

        if (result.about_user) {
            const aboutUser = document.createElement('div');
            aboutUser.className = 'interpretation-text';
            aboutUser.innerHTML = `<strong>About User:</strong> ${result.about_user}`;
            interpretation.appendChild(aboutUser);
        }

        if (result.about_model) {
            const aboutModel = document.createElement('div');
            aboutModel.className = 'interpretation-text';
            aboutModel.innerHTML = `<strong>About Model:</strong> ${result.about_model}`;
            interpretation.appendChild(aboutModel);
        }

        card.appendChild(interpretation);
    }

    return card;
}

/**
 * Update stats panel
 */
function updateStats(query, data) {
    statsContainer.style.display = 'block';
    queryText.textContent = query;

    // Handle both regular and grouped results
    if (data.groups) {
        resultsCount.textContent = `${data.total_groups} groups`;
    } else {
        resultsCount.textContent = data.total_results;
    }

    executionTime.textContent = `${data.execution_time_ms.toFixed(0)}ms`;
}

/**
 * Show loading state
 */
function showLoading() {
    resultsContainer.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Searching conversations...</p>
        </div>
    `;
    statsContainer.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    resultsContainer.innerHTML = `
        <div class="error">
            <strong>Error:</strong> ${message}
        </div>
    `;
    statsContainer.style.display = 'none';
}

/**
 * Show empty state
 */
function showEmptyState(message) {
    resultsContainer.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <h3>No Results</h3>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Truncate text to specified length
 */
function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength) + '...';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
