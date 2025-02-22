// DOM Elements
const searchContainer = document.querySelector('.search-container');
const resultsGrid = document.querySelector('#results');

// Initialize search container
const initSearchContainer = () => {
    // Create and append search elements to the search container
    searchContainer.innerHTML = `
        <div class="max-w-xl mx-auto">
            <div class="flex gap-4">
                <input type="text" 
                       placeholder="Enter product name or URL" 
                       class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <button class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-500 transition-colors">
                    Search
                </button>
            </div>
        </div>
    `;
};

// Product Card Template
const createProductCard = (product) => {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md overflow-hidden product-card';
    card.dataset.productId = product.id;
    card.innerHTML = `
        <div class="relative">
            <img src="${product.image}" alt="${product.name}" 
                 class="w-full h-48 object-cover"/>
            <span class="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded-full text-sm">
                ${product.discount}% OFF
            </span>
        </div>
        <div class="p-4">
            <h3 class="text-lg font-semibold mb-2">${product.name}</h3>
            <div class="flex items-center justify-between mb-2">
                <span class="text-2xl font-bold text-blue-600">$${product.currentPrice}</span>
                <span class="text-gray-500 line-through">$${product.originalPrice}</span>
            </div>
            <div class="flex items-center mb-2">
                <span class="text-sm text-gray-600">Store:</span>
                <span class="ml-2 text-sm font-medium">${product.store}</span>
            </div>
            <button class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-500 transition-colors">
                Track Price
            </button>
        </div>
    `;
    return card;
};

// Search Products
const searchProducts = async (query) => {
    try {
        // Show loading state
        resultsGrid.innerHTML = '<div class="col-span-full text-center">Loading...</div>';

        // Mock API response - replace this with your actual API call
        const mockProducts = [
            {
                id: 1,
                name: "Wireless Headphones",
                currentPrice: 79.99,
                originalPrice: 129.99,
                discount: 38,
                store: "TechStore",
                image: "/api/placeholder/300/200"
            },
            {
                id: 2,
                name: "Smart Watch",
                currentPrice: 199.99,
                originalPrice: 249.99,
                discount: 20,
                store: "ElectroHub",
                image: "/api/placeholder/300/200"
            },
            {
                id: 3,
                name: "Bluetooth Speaker",
                currentPrice: 49.99,
                originalPrice: 69.99,
                discount: 28,
                store: "AudioMart",
                image: "/api/placeholder/300/200"
            }
        ];

        // Clear previous results
        resultsGrid.innerHTML = '';

        // Add new results
        mockProducts.forEach(product => {
            resultsGrid.appendChild(createProductCard(product));
        });

    } catch (error) {
        console.error('Error searching products:', error);
        resultsGrid.innerHTML = `
            <div class="col-span-full text-center text-red-600">
                Error loading products. Please try again.
            </div>
        `;
    }
};

// Price Tracking Function
const trackPrice = async (productId) => {
    // Implement price tracking logic here
    console.log(`Tracking price for product ${productId}`);
    // Show tracking confirmation
    alert('Product added to price tracking!');
};

// Event Listeners
const initEventListeners = () => {
    // Initialize search elements first
    initSearchContainer();

    const searchInput = searchContainer.querySelector('input');
    const searchButton = searchContainer.querySelector('button');

    // Search button click
    searchButton.addEventListener('click', () => {
        const query = searchInput.value.trim();
        if (query) {
            searchProducts(query);
        }
    });

    // Search on Enter key
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                searchProducts(query);
            }
        }
    });

    // Delegate click events for track price buttons
    resultsGrid.addEventListener('click', (e) => {
        if (e.target.matches('button')) {
            const productCard = e.target.closest('.product-card');
            if (productCard) {
                const productId = productCard.dataset.productId;
                trackPrice(productId);
            }
        }
    });
};

// Initialize the application
const init = () => {
    initEventListeners();
};

// Run initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', init);

// Export functions for potential reuse or testing
export {
    searchProducts,
    trackPrice,
    createProductCard
};