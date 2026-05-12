/**
 * CKD Prediction System — Bilingual i18n (English / Hindi)
 * Include this script on any page + call CKDi18n.init()
 * Language is persisted in localStorage('ckd-lang')
 */

const CKDi18n = (() => {

    const translations = {
        // ── Navbar ──
        'nav.home':             { en: 'Home',               hi: 'होम' },
        'nav.dashboard':        { en: 'Dashboard',          hi: 'डैशबोर्ड' },
        'nav.about':            { en: 'About CKD',          hi: 'CKD के बारे में' },
        'nav.understanding':    { en: 'Understanding',      hi: 'समझना' },
        'nav.howItWorks':       { en: 'How It Works',       hi: 'यह कैसे काम करता है' },
        'nav.login':            { en: 'Login',              hi: 'लॉग इन' },
        'nav.signup':           { en: 'Sign Up',            hi: 'साइन अप' },
        'nav.logout':           { en: 'Logout',             hi: 'लॉग आउट' },
        'nav.signedAs':         { en: 'Signed in as',       hi: 'इस रूप में साइन इन' },
        'nav.dashHistory':      { en: 'Dashboard & History', hi: 'डैशबोर्ड और इतिहास' },

        // ── Hero Section ──
        'hero.badge':           { en: 'Advanced Clinical Assessment', hi: 'उन्नत नैदानिक मूल्यांकन' },
        'hero.title':           { en: 'Chronic Kidney Disease Prediction System', hi: 'क्रोनिक किडनी रोग भविष्यवाणी प्रणाली' },
        'hero.subtitle':        { en: 'Advanced CKD risk assessment using Random Forest model trained on UCI clinical dataset with 24 diagnostic parameters.', hi: 'UCI नैदानिक डेटासेट पर 24 नैदानिक मापदंडों के साथ प्रशिक्षित रैंडम फॉरेस्ट मॉडल का उपयोग करके उन्नत CKD जोखिम मूल्यांकन।' },
        'hero.startCheck':      { en: 'Start CKD Check',    hi: 'CKD जांच शुरू करें' },
        'hero.learnMore':       { en: 'Learn More',         hi: 'और जानें' },

        // ── Mode Selection ──
        'mode.title':           { en: 'Select Input Mode',  hi: 'इनपुट मोड चुनें' },
        'mode.patient':         { en: 'Patient Mode',       hi: 'रोगी मोड' },
        'mode.patientDesc':     { en: 'I have basic health information from my doctor', hi: 'मेरे पास अपने डॉक्टर से बुनियादी स्वास्थ्य जानकारी है' },
        'mode.doctor':          { en: 'Doctor Mode',        hi: 'डॉक्टर मोड' },
        'mode.doctorDesc':      { en: 'I have complete lab report with all 24 parameters', hi: 'मेरे पास सभी 24 मापदंडों के साथ पूर्ण लैब रिपोर्ट है' },

        // ── Common Form ──
        'form.patientName':     { en: 'Patient Name',       hi: 'रोगी का नाम' },
        'form.age':             { en: 'Age',                hi: 'उम्र' },
        'form.bloodPressure':   { en: 'Blood Pressure',     hi: 'रक्तचाप' },
        'form.submit':          { en: 'Predict Now',        hi: 'अभी भविष्यवाणी करें' },
        'form.reset':           { en: 'Reset',              hi: 'रीसेट' },
        'form.yes':             { en: 'Yes',                hi: 'हाँ' },
        'form.no':              { en: 'No',                 hi: 'नहीं' },
        'form.normal':          { en: 'Normal',             hi: 'सामान्य' },
        'form.abnormal':        { en: 'Abnormal',           hi: 'असामान्य' },
        'form.good':            { en: 'Good',               hi: 'अच्छा' },
        'form.poor':            { en: 'Poor',               hi: 'खराब' },

        // ── Dashboard Tabs ──
        'dash.dashboard':       { en: 'Dashboard',          hi: 'डैशबोर्ड' },
        'dash.patients':        { en: 'Patients',           hi: 'मरीज़' },
        'dash.models':          { en: 'Models',             hi: 'मॉडल' },
        'dash.analytics':       { en: 'Analytics',          hi: 'विश्लेषण' },
        'dash.settings':        { en: 'Settings',           hi: 'सेटिंग्स' },

        // ── Dashboard Content ──
        'dash.title':           { en: 'Clinical Overview at a Glance', hi: 'एक नज़र में नैदानिक अवलोकन' },
        'dash.subtitle':        { en: 'This dashboard summarizes key working indicators from the latest CKD prediction session.', hi: 'यह डैशबोर्ड नवीनतम CKD भविष्यवाणी सत्र के प्रमुख संकेतकों का सारांश प्रस्तुत करता है।' },
        'dash.lastSession':     { en: 'Patient: Last Session Snapshot', hi: 'रोगी: अंतिम सत्र स्नैपशॉट' },
        'dash.bloodPressure':   { en: 'Blood Pressure',     hi: 'रक्तचाप' },
        'dash.creatinine':      { en: 'Creatinine',         hi: 'क्रिएटिनिन' },
        'dash.eGFR':            { en: 'Estimated eGFR',     hi: 'अनुमानित eGFR' },
        'dash.hemoglobin':      { en: 'Hemoglobin',         hi: 'हीमोग्लोबिन' },
        'dash.riskAnalysis':    { en: 'Risk Analysis & Prediction', hi: 'जोखिम विश्लेषण और भविष्यवाणी' },
        'dash.activity':        { en: 'Patient Activity',   hi: 'रोगी गतिविधि' },
        'dash.recommendations': { en: 'Recommendations',    hi: 'सिफारिशें' },
        'dash.notChecked':      { en: 'Not checked yet.',   hi: 'अभी तक जांच नहीं हुई।' },

        // ── Settings ──
        'settings.theme':       { en: 'Theme & Preferences', hi: 'थीम और प्राथमिकताएं' },
        'settings.selectTheme': { en: 'Select Theme',       hi: 'थीम चुनें' },
        'settings.light':       { en: 'Light',              hi: 'लाइट' },
        'settings.dark':        { en: 'Dark',               hi: 'डार्क' },
        'settings.language':    { en: 'Language',            hi: 'भाषा' },
        'settings.notifications': { en: 'Enable Email Notifications', hi: 'ईमेल सूचनाएं सक्षम करें' },
        'settings.account':     { en: 'Account Details',    hi: 'खाता विवरण' },
        'settings.fullName':    { en: 'Full Name',          hi: 'पूरा नाम' },
        'settings.email':       { en: 'Email Address',      hi: 'ईमेल पता' },
        'settings.profilePic':  { en: 'Profile Picture',    hi: 'प्रोफ़ाइल चित्र' },
        'settings.choosePhoto': { en: '📷 Choose Photo',    hi: '📷 फोटो चुनें' },
        'settings.family':      { en: 'Family Members',     hi: 'परिवार के सदस्य' },

        // ── Results ──
        'result.prediction':    { en: 'Prediction Result',  hi: 'भविष्यवाणी परिणाम' },
        'result.ckd':           { en: 'CKD',                hi: 'CKD (क्रोनिक किडनी रोग)' },
        'result.notCKD':        { en: 'Not CKD',            hi: 'CKD नहीं' },
        'result.probability':   { en: 'CKD Probability',    hi: 'CKD संभावना' },
        'result.lowRisk':       { en: 'Low Risk',           hi: 'कम जोखिम' },
        'result.highRisk':      { en: 'High Risk',          hi: 'उच्च जोखिम' },

        // ── Footer ──
        'footer.title':         { en: 'CKD Prediction System — Advanced Kidney Disease Risk Assessment', hi: 'CKD भविष्यवाणी प्रणाली — उन्नत किडनी रोग जोखिम मूल्यांकन' },
        'footer.dataset':       { en: 'Dataset:', hi: 'डेटासेट:' },

        // ── About CKD Page ──
        'about.badge':          { en: 'Understanding the Disease', hi: 'रोग को समझना' },
        'about.title':          { en: 'Chronic Kidney Disease', hi: 'क्रोनिक किडनी रोग' },
        'about.desc':           { en: 'A comprehensive guide to understanding CKD — its causes, symptoms, global impact, and why early detection can save lives.', hi: 'CKD को समझने के लिए एक व्यापक मार्गदर्शिका — इसके कारण, लक्षण, वैश्विक प्रभाव, और क्यों शीघ्र पहचान जीवन बचा सकती है।' },

        // ── How It Works Page ──
        'how.badge':            { en: 'System Architecture', hi: 'सिस्टम आर्किटेक्चर' },
        'how.title':            { en: 'How It Works',       hi: 'यह कैसे काम करता है' },
        'how.desc':             { en: 'An in-depth look at the technology, models, and clinical research behind our CKD prediction system.', hi: 'हमारी CKD भविष्यवाणी प्रणाली के पीछे की प्रौद्योगिकी, मॉडल और नैदानिक अनुसंधान पर गहन नज़र।' },

        // ── Buttons & Actions ──
        'btn.pdf':              { en: '📄 PDF',              hi: '📄 PDF' },
        'btn.delete':           { en: '🗑️ Delete',          hi: '🗑️ हटाएं' },
        'btn.clearAll':         { en: 'Clear All Records',  hi: 'सभी रिकॉर्ड साफ़ करें' },
        'btn.logout':           { en: '🚪 Logout',          hi: '🚪 लॉग आउट' },
    };

    let currentLang = localStorage.getItem('ckd-lang') || 'en';

    function t(key) {
        const entry = translations[key];
        if (!entry) return key;
        return entry[currentLang] || entry.en || key;
    }

    function applyToPage() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = t(key);
            if (el.tagName === 'INPUT' && el.type !== 'submit') {
                if (el.placeholder) el.placeholder = text;
            } else if (el.tagName === 'OPTION') {
                el.textContent = text;
            } else {
                el.textContent = text;
            }
        });
        // Also handle data-i18n-placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
        });
    }

    function setLang(lang) {
        currentLang = lang;
        localStorage.setItem('ckd-lang', lang);
        applyToPage();
    }

    function getLang() {
        return currentLang;
    }

    function init() {
        currentLang = localStorage.getItem('ckd-lang') || 'en';
        applyToPage();
    }

    return { t, setLang, getLang, init, applyToPage };
})();

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => CKDi18n.init());
} else {
    CKDi18n.init();
}
