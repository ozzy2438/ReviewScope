/**
 * Main JavaScript for Amazon Scraper & Analyzer
 */

$(document).ready(function() {
    // Job status polling for results page
    if ($('#job-status-container').length) {
        const jobId = $('#job-status-container').data('job-id');
        
        // Poll for job status updates
        const statusInterval = setInterval(function() {
            $.getJSON(`/api/job-status/${jobId}`, function(data) {
                // Update progress bar
                $('#progress-bar')
                    .css('width', data.progress + '%')
                    .attr('aria-valuenow', data.progress)
                    .text(data.progress + '%');
                
                // Update status text
                $('#job-status').text(data.status);
                
                // If job is completed, show dashboard link and stop polling
                if (data.status === 'completed') {
                    clearInterval(statusInterval);
                    $('#dashboard-link-container').removeClass('d-none');
                }
                
                // If job failed, show error and stop polling
                if (data.status === 'failed') {
                    clearInterval(statusInterval);
                    $('#error-container').removeClass('d-none').find('.error-message').text(data.error);
                }
            });
        }, 2000); // Poll every 2 seconds
    }
    
    // Word Cloud visualization for dashboard page
    if ($('#word-cloud').length) {
        const wordCloudData = JSON.parse($('#word-cloud').attr('data-words'));
        
        // Set up word cloud layout
        const layout = d3.layout.cloud()
            .size([400, 300])
            .words(wordCloudData)
            .padding(5)
            .rotate(function() { return ~~(Math.random() * 2) * 90; })
            .font("Arial")
            .fontSize(function(d) { return Math.sqrt(d.value) * 5; })
            .on("end", draw);
            
        layout.start();
        
        function draw(words) {
            d3.select("#word-cloud").append("svg")
                .attr("width", layout.size()[0])
                .attr("height", layout.size()[1])
                .append("g")
                .attr("transform", "translate(" + layout.size()[0] / 2 + "," + layout.size()[1] / 2 + ")")
                .selectAll("text")
                .data(words)
                .enter().append("text")
                .style("font-size", function(d) { return d.size + "px"; })
                .style("fill", function(d) { 
                    // Color based on word frequency
                    const colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"];
                    return colors[Math.floor(Math.random() * colors.length)]; 
                })
                .attr("text-anchor", "middle")
                .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                })
                .text(function(d) { return d.text; });
        }
    }
    
    // Initialize Plotly charts on dashboard
    if ($('.plotly-chart').length) {
        $('.plotly-chart').each(function() {
            const chartData = JSON.parse($(this).attr('data-chart'));
            Plotly.newPlot(this.id, chartData.data, chartData.layout);
        });
    }
});

// Global utilities
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Animate elements when they come into view
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.animate-on-scroll');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 50) {
                element.classList.add('animated');
            }
        });
    };

    // Run once on load
    animateOnScroll();
    
    // Add scroll event listener
    window.addEventListener('scroll', animateOnScroll);

    // Add dashboard-card class to cards in dashboard
    if (window.location.pathname.includes('/dashboard/')) {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            if (!card.classList.contains('dashboard-card') && 
                !card.closest('.dashboard-summary')) {
                card.classList.add('dashboard-card');
            }
        });
    }
}); 