/**
 * VOX - Space Edition: Cosmic Background Starfield
 * Renders an ultra-smooth, lightweight dynamic starfield canvas
 * with twinkling stars, cosmic dust particles, and shooting stars.
 */

(function initSpaceStarfield() {
    const canvas = document.createElement('canvas');
    canvas.id = 'space-starfield';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    canvas.style.opacity = '0.75';
    document.body.prepend(canvas);

    const ctx = canvas.getContext('2d');
    let width = 0;
    let height = 0;
    let stars = [];
    let shootingStars = [];
    let animationFrameId = null;

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        initStars();
    }

    function initStars() {
        stars = [];
        const count = Math.floor((width * height) / 8000); // Responsive density
        const colors = ['#ffffff', '#c7d2fe', '#818cf8', '#06b6d4', '#e0e7ff'];

        for (let i = 0; i < count; i++) {
            stars.push({
                x: Math.random() * width,
                y: Math.random() * height,
                radius: Math.random() * 1.5 + 0.3,
                color: colors[Math.floor(Math.random() * colors.length)],
                alpha: Math.random() * 0.8 + 0.2,
                twinkleSpeed: (Math.random() * 0.02 + 0.005) * (Math.random() > 0.5 ? 1 : -1),
            });
        }
    }

    function spawnShootingStar() {
        if (shootingStars.length < 2 && Math.random() < 0.015) {
            shootingStars.push({
                x: Math.random() * width,
                y: Math.random() * (height * 0.5),
                len: Math.random() * 80 + 40,
                speed: Math.random() * 10 + 6,
                angle: Math.PI / 4 + (Math.random() - 0.5) * 0.2,
                alpha: 1,
            });
        }
    }

    function render() {
        ctx.clearRect(0, 0, width, height);

        // Draw and twinkle stars
        for (let i = 0; i < stars.length; i++) {
            const star = stars[i];
            star.alpha += star.twinkleSpeed;
            if (star.alpha > 0.95 || star.alpha < 0.15) {
                star.twinkleSpeed = -star.twinkleSpeed;
            }

            ctx.beginPath();
            ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
            ctx.fillStyle = star.color;
            ctx.globalAlpha = Math.max(0.1, Math.min(1, star.alpha));
            ctx.shadowBlur = star.radius > 1.2 ? 6 : 0;
            ctx.shadowColor = star.color;
            ctx.fill();
        }

        // Draw shooting stars
        spawnShootingStar();
        for (let i = shootingStars.length - 1; i >= 0; i--) {
            const ss = shootingStars[i];
            ctx.beginPath();
            ctx.moveTo(ss.x, ss.y);
            const tailX = ss.x - Math.cos(ss.angle) * ss.len;
            const tailY = ss.y - Math.sin(ss.angle) * ss.len;
            ctx.lineTo(tailX, tailY);

            const grad = ctx.createLinearGradient(ss.x, ss.y, tailX, tailY);
            grad.addColorStop(0, `rgba(6, 182, 212, ${ss.alpha})`);
            grad.addColorStop(0.5, `rgba(99, 102, 241, ${ss.alpha * 0.6})`);
            grad.addColorStop(1, 'rgba(255, 255, 255, 0)');

            ctx.strokeStyle = grad;
            ctx.lineWidth = 1.8;
            ctx.shadowBlur = 10;
            ctx.shadowColor = '#06b6d4';
            ctx.stroke();

            ss.x += Math.cos(ss.angle) * ss.speed;
            ss.y += Math.sin(ss.angle) * ss.speed;
            ss.alpha -= 0.015;

            if (ss.alpha <= 0 || ss.x > width || ss.y > height) {
                shootingStars.splice(i, 1);
            }
        }

        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;

        animationFrameId = requestAnimationFrame(render);
    }

    window.addEventListener('resize', resize);
    window.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            if (animationFrameId) cancelAnimationFrame(animationFrameId);
        } else {
            animationFrameId = requestAnimationFrame(render);
        }
    });

    resize();
    render();
})();
