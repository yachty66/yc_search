// Load the JSON data
let companiesData = [];
let currentPage = 0;
const itemsPerPage = 12;
let isLoading = false;

// Function to load the JSON data
async function loadJSONData() {
    try {
        const response = await fetch('data/all.json');
        companiesData = await response.json();
        loadCompanyData();
    } catch (error) {
        console.error('Error loading JSON:', error);
    }
}

// Function to render company cards
function renderCompanyCards(companies) {
    const companiesGrid = document.getElementById("companies-grid");
    
    companies.forEach((company) => {
        const companyCard = document.createElement("div");
        companyCard.className = "bg-white p-4 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300 cursor-pointer";
        
        // Add click handler to the card
        companyCard.addEventListener('click', () => {
            const modalHTML = createCompanyModal(company);
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        });

        const uniqueTags = [...new Set(company.tags)];
        const blueTags = uniqueTags.filter((tag) => tag !== "Active");

        companyCard.innerHTML = `
            <div class="flex flex-col items-center">
                <img src="${company.logo}" alt="${company.company_name} Logo" 
                     class="w-24 h-24 rounded-lg mb-3 border border-gray-200"
                     onerror="this.onerror=null; this.src='placeholder.png';">
                <div class="text-center">
                    <h3 class="font-semibold text-lg text-gray-900">${company.company_name}</h3>
                    <div class="flex flex-wrap gap-1 justify-center">
                        ${blueTags
                            .map(tag => `
                                <span class="text-xs bg-[#FFF1EB] text-[#FF4F00] px-3 py-1 rounded-full hover:bg-[#FFE4D9] transition-colors">
                                    ${tag}
                                </span>
                            `)
                            .join("")}
                    </div>
                </div>
            </div>
        `;

        companiesGrid.appendChild(companyCard);
    });
}

// Function to load company data with pagination
async function loadCompanyData() {
    if (isLoading) return;
    isLoading = true;

    const start = currentPage * itemsPerPage;
    const end = start + itemsPerPage;
    const pageCompanies = companiesData.slice(start, end);

    renderCompanyCards(pageCompanies);
    currentPage++;
    isLoading = false;
}

// Handle scroll event for infinite scrolling
function handleScroll() {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
        loadCompanyData();
    }
}

// Add these new functions at the bottom of the file
async function handleSearch(event) {
    event.preventDefault();
    const searchInput = document.getElementById('search-bar');
    const companiesGrid = document.getElementById('companies-grid');
    
    if (searchInput && searchInput.value.trim()) {
        // Show loading state
        companiesGrid.innerHTML = `
            <div class="col-span-full flex justify-center items-center py-20">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                <span class="ml-3 text-gray-600">Searching companies...</span>
            </div>
        `;

        try {
            const response = await fetch('/api/query_local', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: searchInput.value.trim()
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const matchedCompanies = await response.json();
            
            // Clear the grid
            companiesGrid.innerHTML = '';

            if (matchedCompanies.length === 0) {
                companiesGrid.innerHTML = `
                    <div class="col-span-full text-center py-10">
                        <p class="text-gray-600">No companies found matching your search.</p>
                    </div>
                `;
                return;
            }

            // Render the matched companies
            renderCompanyCards(matchedCompanies);

        } catch (error) {
            console.error('Error searching companies:', error);
            companiesGrid.innerHTML = `
                <div class="col-span-full text-center py-10">
                    <p class="text-red-600">Error searching companies. Please try again.</p>
                </div>
            `;
        }
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    loadJSONData();
    
    // Add search button event listener
    const searchButton = document.getElementById('search-button');
    if (searchButton) {
        searchButton.addEventListener('click', handleSearch);
    } else {
        console.error('Search button not found!');
    }
});

// Add scroll event listener
window.addEventListener("scroll", handleScroll);

// Add this function to create the modal HTML
function createCompanyModal(company) {
    return `
        <div id="company-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <!-- Modal Header -->
                <div class="border-b px-6 py-4 flex items-center justify-between">
                    <h2 class="text-2xl font-bold text-gray-900">${company.company_name}</h2>
                    <button onclick="closeModal()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                
                <!-- Modal Content -->
                <div class="px-6 py-4">
                    <div class="flex items-start gap-6 mb-6">
                        <img src="${company.logo}" 
                             alt="${company.company_name} Logo"
                             class="w-24 h-24 rounded-lg border border-gray-200"
                             onerror="this.onerror=null; this.src='placeholder.png';">
                        <div>
                            <div class="flex flex-wrap gap-2 mb-3">
                                ${company.tags
                                    .filter(tag => tag !== 'Active')
                                    .map(tag => `
                                        <span class="text-sm bg-[#FFF1EB] text-[#FF4F00] px-3 py-1 rounded-full">
                                            ${tag}
                                        </span>
                                    `).join('')}
                            </div>
                            <p class="text-gray-600">${company.description || 'No description available.'}</p>
                        </div>
                    </div>
                    
                    <div class="space-y-4">
                        <div class="grid grid-cols-3 gap-4">
                            <div>
                                <h3 class="font-semibold text-gray-900">Founded</h3>
                                <p class="text-gray-600">${company.founded_year || 'N/A'}</p>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-900">Team Size</h3>
                                <p class="text-gray-600">${company.team_size ? company.team_size + ' people' : 'N/A'}</p>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-900">Location</h3>
                                <p class="text-gray-600">${company.location || 'N/A'}</p>
                            </div>
                        </div>
                        
                        ${company.founders?.length ? `
                            <div>
                                <h3 class="font-semibold text-gray-900 mb-2">Founders</h3>
                                <div class="space-y-2">
                                    ${company.founders.map(founder => `
                                        <div>
                                            <p class="text-gray-900">${founder.name}</p>
                                            <div class="flex gap-2">
                                                ${Object.entries(founder.social_links || {}).map(([platform, url]) => `
                                                    <a href="${url}" 
                                                       target="_blank" 
                                                       rel="noopener noreferrer"
                                                       class="text-sm text-[#FF4F00] hover:text-[#E64600]">
                                                        ${platform}
                                                    </a>
                                                `).join('')}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${company.company_socials && Object.keys(company.company_socials).length ? `
                            <div>
                                <h3 class="font-semibold text-gray-900 mb-2">Company Social Media</h3>
                                <div class="flex flex-wrap gap-2">
                                    ${Object.entries(company.company_socials).map(([platform, url]) => `
                                        <a href="${url}" 
                                           target="_blank" 
                                           rel="noopener noreferrer"
                                           class="text-sm text-[#FF4F00] hover:text-[#E64600]">
                                            ${platform}
                                        </a>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${company.company_url ? `
                            <div>
                                <h3 class="font-semibold text-gray-900 mb-2">Company Website</h3>
                                <a href="${company.company_url}" 
                                   target="_blank" 
                                   rel="noopener noreferrer"
                                   class="text-[#FF4F00] hover:text-[#E64600]">
                                    ${company.company_url}
                                </a>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Add these functions to handle modal open/close
function closeModal() {
    const modal = document.getElementById('company-modal');
    if (modal) {
        modal.remove();
    }
}

// Add event listener to close modal when clicking outside
document.addEventListener('click', (event) => {
    const modal = document.getElementById('company-modal');
    if (modal && event.target === modal) {
        closeModal();
    }
});