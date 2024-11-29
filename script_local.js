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
        companyCard.className = "bg-white p-4 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300";

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
                                <span class="text-xs bg-blue-100 text-blue-800 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors">
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