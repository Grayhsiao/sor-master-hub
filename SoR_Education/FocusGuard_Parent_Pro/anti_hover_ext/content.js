// Aggressively remove any video elements that spawn inside preview containers
function blockPreviews() {
    const previewContainers = document.querySelectorAll('ytd-video-preview, #inline-preview-player, ytd-inline-preview-player, .ytd-video-preview, ytd-thumbnail-overlay-video-preview-renderer');
    previewContainers.forEach(container => {
        container.style.display = 'none';
        container.style.pointerEvents = 'none';
        const videos = container.querySelectorAll('video');
        videos.forEach(v => {
            v.pause();
            v.src = '';
            v.remove();
        });
    });
}

// Run immediately and then frequently
blockPreviews();
setInterval(blockPreviews, 300);

console.log("🛡️ Focus Guard Anti-Hover Extension Active (v2)");
