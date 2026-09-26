<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>PulseTap - Tap to Earn</title>
    <!-- Telegram WebApp SDK -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <!-- Tailwind CSS for Modern UI -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        body {
            user-select: none;
            -webkit-user-select: none;
            background: #0d1117;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }
        .tap-coin {
            transition: transform 0.05s ease;
            box-shadow: 0 0 50px rgba(234, 179, 8, 0.3);
        }
        .tap-coin:active {
            transform: scale(0.95);
        }
        .floating-text {
            position: absolute;
            animation: floatUp 0.8s ease-out forwards;
            font-weight: bold;
            color: #facc15;
            pointer-events: none;
            font-size: 24px;
            text-shadow: 0 0 10px rgba(0,0,0,0.8);
        }
        @keyframes floatUp {
            0% { opacity: 1; transform: translateY(0) scale(1); }
            100% { opacity: 0; transform: translateY(-80px) scale(1.2); }
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body class="flex flex-col h-screen justify-between p-4 max-w-md mx-auto">

    <!-- TOP BAR: User Profile & Total Balance -->
    <div>
        <div class="flex items-center justify-between glass-card p-3 rounded-2xl mb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-gradient-to-r from-amber-500 to-yellow-300 flex items-center justify-center font-bold text-black text-lg" id="user-avatar">
                    U
                </div>
                <div>
                    <h2 class="text-sm font-semibold leading-tight" id="user-name">Telegram User</h2>
                    <span class="text-xs text-yellow-400 font-medium"><i class="fa-solid fa-shield-halved"></i> Verified Miner</span>
                </div>
            </div>
            <div class="bg-yellow-500/10 border border-yellow-500/30 px-3 py-1 rounded-full text-xs text-yellow-400 font-bold">
                VIP Lv. <span id="vip-level">1</span>
            </div>
        </div>

        <!-- Coin Balance Header -->
        <div class="text-center my-2">
            <div class="text-gray-400 text-xs tracking-widest uppercase mb-1">Total Balance</div>
            <div class="flex items-center justify-center gap-2 text-4xl font-extrabold text-yellow-400 tracking-wider">
                <i class="fa-solid fa-coins text-yellow-500"></i>
                <span id="balance">0</span>
            </div>
        </div>
    </div>

    <!-- TAB 1: TAP GAME MAIN SECTION -->
    <div id="tab-tap" class="tab-content flex flex-col items-center justify-center flex-grow my-auto">
        <!-- Coin Button -->
        <div class="relative">
            <div id="coin" class="tap-coin w-60 h-60 rounded-full bg-gradient-to-b from-yellow-300 via-amber-500 to-yellow-600 p-3 flex items-center justify-center cursor-pointer border-4 border-yellow-200">
                <div class="w-full h-full rounded-full bg-gradient-to-b from-amber-600 to-yellow-800 flex items-center justify-center border-2 border-yellow-300/50">
                    <i class="fa-solid fa-bolt text-7xl text-yellow-200 drop-shadow-lg"></i>
                </div>
            </div>
        </div>

        <!-- Energy Bar -->
        <div class="w-full mt-8 glass-card p-3 rounded-xl">
            <div class="flex justify-between text-xs mb-1">
                <span class="text-gray-300"><i class="fa-solid fa-bolt text-yellow-400 mr-1"></i> Energy</span>
                <span class="font-bold text-yellow-400"><span id="energy">1000</span> / <span id="max-energy">1000</span></span>
            </div>
            <div class="w-full bg-gray-800 h-3 rounded-full overflow-hidden p-0.5 border border-white/10">
                <div id="energy-bar" class="bg-gradient-to-r from-yellow-500 to-amber-300 h-full rounded-full transition-all duration-200" style="width: 100%;"></div>
            </div>
        </div>
    </div>

    <!-- TAB 2: WATCH ADS SECTION (5-Ad Boost) -->
    <div id="tab-ads" class="tab-content hidden flex-grow my-auto flex flex-col justify-center">
        <div class="glass-card p-5 rounded-2xl text-center border border-amber-500/20">
            <div class="w-16 h-16 bg-amber-500/20 text-amber-400 rounded-full flex items-center justify-center mx-auto text-2xl mb-3">
                <i class="fa-solid fa-play"></i>
            </div>
            <h3 class="text-lg font-bold text-yellow-400">Watch 5 Ads for Instant Energy</h3>
            <p class="text-xs text-gray-400 mt-1 mb-4">৫টি সংক্ষিপ্ত ভিডিও বিজ্ঞাপন দেখলে আপনার পুরো অ্যানার্জি সাথে সাথে ১০০% রিফিল হয়ে যাবে!</p>
            
            <!-- Progress Tracker -->
            <div class="mb-4">
                <div class="text-xs text-gray-300 mb-1">Ads Completed: <span id="ads-count" class="text-yellow-400 font-bold">0</span>/5</div>
                <div class="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                    <div id="ads-progress" class="bg-yellow-500 h-full w-0 transition-all"></div>
                </div>
            </div>

            <button onclick="watchAd()" id="ad-btn" class="w-full py-3 bg-gradient-to-r from-amber-500 to-yellow-500 font-bold text-black rounded-xl shadow-lg active:scale-95 transition">
                <i class="fa-solid fa-circle-play mr-2"></i> Watch Ad Now (+1)
            </button>
        </div>
    </div>

    <!-- TAB 3: IN-APP PURCHASE / TELEGRAM STARS (VIP SHOP) -->
    <div id="tab-shop" class="tab-content hidden flex-grow my-auto overflow-y-auto max-h-[60vh] pr-1">
        <h3 class="text-sm font-bold text-gray-400 mb-3 uppercase tracking-wider">Telegram Stars Store</h3>
        
        <!-- Item 1: Auto Tap Bot -->
        <div class="glass-card p-4 rounded-xl mb-3 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center text-blue-400 text-xl">
                    <i class="fa-solid fa-robot"></i>
                </div>
                <div>
                    <h4 class="font-bold text-sm">Auto-Miner Bot</h4>
                    <p class="text-xs text-gray-400">অফলাইনে স্বয়ংক্রিয়ভাবে কয়েন মাইন করবে</p>
                </div>
            </div>
            <button onclick="buyWithStars('Auto-Miner Bot', 50)" class="bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-bold text-xs px-3 py-2 rounded-lg flex items-center gap-1 active:scale-95">
                50 <i class="fa-solid fa-star text-yellow-300"></i>
            </button>
        </div>

        <!-- Item 2: Energy Capacity Upgrade -->
        <div class="glass-card p-4 rounded-xl mb-3 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center text-yellow-400 text-xl">
                    <i class="fa-solid fa-battery-full"></i>
                </div>
                <div>
                    <h4 class="font-bold text-sm">Max Energy +2000</h4>
                    <p class="text-xs text-gray-400">অ্যানার্জি লিমিট স্থায়ীভাবে বৃদ্ধি করুন</p>
                </div>
            </div>
            <button onclick="buyWithStars('Max Energy Booster', 100)" class="bg-gradient-to-r from-yellow-500 to-amber-500 text-black font-bold text-xs px-3 py-2 rounded-lg flex items-center gap-1 active:scale-95">
                100 <i class="fa-solid fa-star text-black"></i>
            </button>
        </div>

        <!-- Item 3: VIP Supporter Pass -->
        <div class="glass-card p-4 rounded-xl mb-3 flex items-center justify-between border border-purple-500/30">
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center text-purple-400 text-xl">
                    <i class="fa-solid fa-crown"></i>
                </div>
                <div>
                    <h4 class="font-bold text-sm text-purple-300">VIP Pro Membership</h4>
                    <p class="text-xs text-gray-400">২X ট্যাপ পাওয়ার + গোল্ডেন ব্যাজ</p>
                </div>
            </div>
            <button onclick="buyWithStars('VIP Membership', 250)" class="bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold text-xs px-3 py-2 rounded-lg flex items-center gap-1 active:scale-95">
                250 <i class="fa-solid fa-star text-yellow-300"></i>
            </button>
        </div>
    </div>

    <!-- TAB 4: REFERRAL SYSTEM -->
    <div id="tab-friends" class="tab-content hidden flex-grow my-auto flex flex-col justify-center">
        <div class="glass-card p-5 rounded-2xl text-center">
            <div class="w-16 h-16 bg-green-500/20 text-green-400 rounded-full flex items-center justify-center mx-auto text-2xl mb-3">
                <i class="fa-solid fa-users"></i>
            </div>
            <h3 class="text-lg font-bold text-green-400">Invite Friends & Earn</h3>
            <p class="text-xs text-gray-400 mt-1 mb-4">প্রতিটি সফল ইনভাইটে পান <b class="text-yellow-400">+5,000 Bonus Coins</b>!</p>

            <div class="bg-black/40 p-3 rounded-xl flex items-center justify-between border border-white/10 mb-4">
                <input id="ref-link" type="text" readonly value="https://t.me/PulseTapBot?start=ref_12345" class="bg-transparent text-xs text-gray-300 w-full outline-none">
                <button onclick="copyRefLink()" class="bg-green-500 text-black text-xs font-bold px-3 py-1.5 rounded-lg ml-2 active:scale-95">
                    Copy
                </button>
            </div>

            <button onclick="shareRefLink()" class="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 font-bold text-black rounded-xl shadow-lg active:scale-95">
                <i class="fa-paper-plane mr-1"></i> Send Invite via Telegram
            </button>
        </div>
    </div>

    <!-- BOTTOM NAVIGATION BAR -->
    <div class="glass-card rounded-2xl p-2 flex justify-around items-center border border-white/10 mt-2">
        <button onclick="switchTab('tap')" id="nav-tap" class="flex flex-col items-center gap-1 text-yellow-400 text-xs font-medium">
            <i class="fa-solid fa-hand-pointer text-lg"></i> Tap
        </button>
        <button onclick="switchTab('ads')" id="nav-ads" class="flex flex-col items-center gap-1 text-gray-400 text-xs font-medium">
            <i class="fa-solid fa-circle-play text-lg"></i> Ads
        </button>
        <button onclick="switchTab('shop')" id="nav-shop" class="flex flex-col items-center gap-1 text-gray-400 text-xs font-medium">
            <i class="fa-solid fa-store text-lg"></i> Stars Shop
        </button>
        <button onclick="switchTab('friends')" id="nav-friends" class="flex flex-col items-center gap-1 text-gray-400 text-xs font-medium">
            <i class="fa-solid fa-user-plus text-lg"></i> Friends
        </button>
    </div>

    <!-- JAVASCRIPT LOGIC -->
    <script>
        // Init Telegram WebApp SDK
        const tg = window.Telegram?.WebApp;
        if(tg) {
            tg.expand();
            tg.ready();
            // Set User Data from Telegram
            if(tg.initDataUnsafe?.user) {
                const user = tg.initDataUnsafe.user;
                document.getElementById('user-name').innerText = user.first_name + (user.last_name ? ' ' + user.last_name : '');
                document.getElementById('user-avatar').innerText = user.first_name.charAt(0).toUpperCase();
            }
        }

        // Game State Variables
        let balance = parseInt(localStorage.getItem('balance')) || 0;
        let energy = parseInt(localStorage.getItem('energy')) || 1000;
        let maxEnergy = 1000;
        let adsWatched = 0;
        let tapPower = 1;

        // UI Updates
        const balanceEl = document.getElementById('balance');
        const energyEl = document.getElementById('energy');
        const energyBar = document.getElementById('energy-bar');

        function updateUI() {
            balanceEl.innerText = balance.toLocaleString();
            energyEl.innerText = energy;
            energyBar.style.width = (energy / maxEnergy * 100) + '%';
            localStorage.setItem('balance', balance);
            localStorage.setItem('energy', energy);
        }
        updateUI();

        // Tapping Mechanism
        const coin = document.getElementById('coin');
        coin.addEventListener('click', (e) => {
            if (energy >= tapPower) {
                balance += tapPower;
                energy -= tapPower;
                updateUI();

                // Vibration Feedback (Telegram Haptic)
                if (tg && tg.HapticFeedback) {
                    tg.HapticFeedback.impactOccurred('light');
                }

                // Floating Text FX
                createFloatingText(e.clientX, e.clientY, `+${tapPower}`);
            }
        });

        function createFloatingText(x, y, text) {
            const el = document.createElement('div');
            el.className = 'floating-text';
            el.innerText = text;
            el.style.left = `${x - 15}px`;
            el.style.top = `${y - 30}px`;
            document.body.appendChild(el);
            setTimeout(() => el.remove(), 800);
        }

        // Auto Energy Recovery (1 Energy per second)
        setInterval(() => {
            if (energy < maxEnergy) {
                energy = Math.min(maxEnergy, energy + 1);
                updateUI();
            }
        }, 1000);

        // Ads Mechanism (AdsGram SDK Integration point)
        function watchAd() {
            const btn = document.getElementById('ad-btn');
            btn.innerText = "Watching Ad...";
            btn.disabled = true;

            // Simulate Video Ad Callback
            setTimeout(() => {
                adsWatched++;
                document.getElementById('ads-count').innerText = adsWatched;
                document.getElementById('ads-progress').style.width = (adsWatched / 5 * 100) + '%';

                if (adsWatched >= 5) {
                    energy = maxEnergy;
                    updateUI();
                    alert("🎉 অভিনন্দন! ৫টি অ্যাড সম্পূর্ণ করে আপনি ১০০% এনার্জি রিফিল পেয়েছেন!");
                    adsWatched = 0;
                    document.getElementById('ads-count').innerText = 0;
                    document.getElementById('ads-progress').style.width = '0%';
                } else {
                    alert(`অ্যাড সম্পূর্ণ হয়েছে! (${adsWatched}/5)`);
                }

                btn.innerHTML = `<i class="fa-solid fa-circle-play mr-2"></i> Watch Ad Now (+1)`;
                btn.disabled = false;
            }, 2500);
        }

        // Telegram Stars Purchase System
        function buyWithStars(itemName, starsCount) {
            if (tg && tg.openInvoice) {
                // Real Telegram Stars Invoice Integration Point
                tg.showAlert(`পেমেন্ট প্রসেস করা হচ্ছে: ${itemName} for ${starsCount} Stars ⭐`);
            } else {
                // Fallback simulation for browser test
                if(confirm(`${itemName} কেনার জন্য ${starsCount} Telegram Stars লাগবে। আপনি কি নিশ্চিত?`)) {
                    alert(`সফলভাবে ${itemName} কেনা হয়েছে!`);
                    if(itemName.includes('VIP')) {
                        tapPower = 2;
                        document.getElementById('vip-level').innerText = "2";
                    } else if(itemName.includes('Energy')) {
                        maxEnergy += 2000;
                        energy = maxEnergy;
                        document.getElementById('max-energy').innerText = maxEnergy;
                        updateUI();
                    }
                }
            }
        }

        // Navigation Tabs Controller
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.getElementById(`tab-${tab}`).classList.remove('hidden');

            document.querySelectorAll('button[id^="nav-"]').forEach(el => {
                el.classList.remove('text-yellow-400');
                el.classList.add('text-gray-400');
            });
            document.getElementById(`nav-${tab}`).classList.add('text-yellow-400');
            document.getElementById(`nav-${tab}`).classList.remove('text-gray-400');
        }

        // Referral Handlers
        function copyRefLink() {
            const linkInput = document.getElementById('ref-link');
            linkInput.select();
            navigator.clipboard.writeText(linkInput.value);
            alert("রেফারেল লিংক কপি হয়েছে!");
        }

        function shareRefLink() {
            const link = document.getElementById('ref-link').value;
            const text = `🚀 Join PulseTap Mining & get free crypto bonus!`;
            if (tg) {
                tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`);
            }
        }
    </script>
</body>
</html>
