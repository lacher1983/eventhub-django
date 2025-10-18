class InteractiveVideoPlayer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentVideo = null;
        this.isPlaying = false;
        
        this.init();
    }
    
    init() {
        this.createPlayer();
        this.bindEvents();
    }
    
    createPlayer() {
        this.player = document.createElement('div');
        this.player.className = 'interactive-video-player';
        this.player.innerHTML = `
            <div class="video-container">
                <div class="video-wrapper" id="videoWrapper"></div>
                <div class="video-controls">
                    <button class="btn btn-control btn-play-pause">
                        <i class="fas fa-play"></i>
                    </button>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                    </div>
                    <div class="time-display">
                        <span class="current-time">0:00</span> / 
                        <span class="total-time">0:00</span>
                    </div>
                    <button class="btn btn-control btn-fullscreen">
                        <i class="fas fa-expand"></i>
                    </button>
                    <button class="btn btn-control btn-volume">
                        <i class="fas fa-volume-up"></i>
                    </button>
                </div>
            </div>
            <div class="video-playlist"></div>
        `;
        
        this.container.appendChild(this.player);
        this.videoWrapper = this.player.querySelector('#videoWrapper');
    }
    
    loadVideo(videoUrl, videoType, videoId) {
        // Очищаем предыдущее видео
        this.videoWrapper.innerHTML = '';
        
        if (videoType === 'youtube' || videoType === 'vimeo') {
            this.loadEmbedVideo(videoUrl, videoType);
        } else {
            this.loadHTML5Video(videoUrl);
        }
        
        this.currentVideoId = videoId;
        this.trackVideoLoad();
    }
    
    loadEmbedVideo(url, type) {
        const iframe = document.createElement('iframe');
        iframe.src = url;
        iframe.allowFullscreen = true;
        iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
        iframe.className = 'w-100 h-100';
        
        this.videoWrapper.appendChild(iframe);
        this.currentVideo = iframe;
    }
    
    loadHTML5Video(url) {
        const video = document.createElement('video');
        video.src = url;
        video.controls = true;
        video.className = 'w-100 h-100';
        
        video.addEventListener('loadedmetadata', () => {
            this.updateDuration(video.duration);
        });
        
        video.addEventListener('timeupdate', () => {
            this.updateProgress(video.currentTime, video.duration);
        });
        
        video.addEventListener('play', () => {
            this.setPlayingState(true);
            this.trackVideoPlay();
        });
        
        video.addEventListener('pause', () => {
            this.setPlayingState(false);
        });
        
        this.videoWrapper.appendChild(video);
        this.currentVideo = video;
    }
    
    trackVideoLoad() {
        fetch('/api/video-analytics/load/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_id: this.currentVideoId,
                timestamp: new Date().toISOString()
            })
        });
    }
    
    trackVideoPlay() {
        fetch('/api/video-analytics/play/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_id: this.currentVideoId,
                timestamp: new Date().toISOString()
            })
        });
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Инициализация видеоплеера
document.addEventListener('DOMContentLoaded', function() {
    // Обработчик для кнопок воспроизведения
    document.querySelectorAll('[data-action="play-video"]').forEach(button => {
        button.addEventListener('click', function() {
            const videoWrapper = this.closest('.video-wrapper');
            const video = videoWrapper.querySelector('video');
            const overlay = videoWrapper.querySelector('.video-overlay');
            
            if (video && overlay) {
                video.play();
                video.controls = true;
                overlay.style.display = 'none';

                // Отправка статистики
                const eventId = videoWrapper.dataset.eventId;
                const csrfToken = videoWrapper.dataset.csrfToken;
                
                if (eventId && csrfToken) {
                    fetch(`/api/events/${eventId}/promo-video/view/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'Content-Type': 'application/json',
                        }
                    });
                }
            }
        });
    });
});