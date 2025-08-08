
// Dashboard Fix - Missing Functions
(function() {
    // Make functions globally available
    window.toggleView = function(view) {
        const views = ['kanban', 'list', 'team'];
        views.forEach(v => {
            const element = document.getElementById(v + 'View');
            if (element) {
                element.style.display = (v === view) ? 'block' : 'none';
            }
        });
        
        // Update active button
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.toLowerCase().includes(view)) {
                btn.classList.add('active');
            }
        });
    };
    
    window.checkDebug = async function() {
        try {
            const userId = window.userId || localStorage.getItem('userId') || 'unknown';
            const res = await fetch('/api/debug?user_id=' + userId);
            const data = await res.json();
            console.log('Debug info:', data);
            
            alert('Debug Information:\n' +
                  '==================\n' +
                  'User ID: ' + (data.user_id || 'Not set') + '\n' +
                  'Articles: ' + (data.user_articles_count || 0) + '\n' +
                  'Database: ' + (data.firestore_status || 'Unknown') + '\n' +
                  'Session: ' + (data.session_valid ? 'Valid' : 'Invalid'));
        } catch (error) {
            console.error('Debug error:', error);
            alert('Error fetching debug info: ' + error.message);
        }
    };
    
    // Initialize default view
    document.addEventListener('DOMContentLoaded', function() {
        // Set default view to kanban
        if (window.toggleView) {
            window.toggleView('kanban');
        }
    });
})();
