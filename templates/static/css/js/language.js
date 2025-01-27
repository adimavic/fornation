document.addEventListener('DOMContentLoaded', () => {
    // Language selection dropdown
    const languageDropdown = document.getElementById('language');

    // Text content for each language
    const translations = {
        en: {
            title: "Welcome to the Website",
            description: "This website allows you to dynamically change the language.",
            inputLabel: "Enter your text:",
            inputPlaceholder: "Type something here...",
            submitButton: "Submit",
        },
        hi: {
            title: "वेबसाइट में आपका स्वागत है",
            description: "यह वेबसाइट आपको भाषा को गतिशील रूप से बदलने की अनुमति देती है।",
            inputLabel: "अपना पाठ दर्ज करें:",
            inputPlaceholder: "यहां कुछ टाइप करें...",
            submitButton: "जमा करें",
        },
    };

    // Function to update the text on the page
    function updateLanguage(lang) {
        const translation = translations[lang];
        if (translation) {
            document.getElementById('title').textContent = translation.title;
            document.getElementById('description').textContent = translation.description;
            document.getElementById('inputLabel').textContent = translation.inputLabel;
            document.getElementById('inputField').placeholder = translation.inputPlaceholder;
            document.getElementById('submitButton').textContent = translation.submitButton;
        }
    }

    // Event listener for language change
    languageDropdown.addEventListener('change', (event) => {
        const selectedLanguage = event.target.value;
        updateLanguage(selectedLanguage);
    });

    // Initial language update based on default dropdown value
    updateLanguage(languageDropdown.value);
});
