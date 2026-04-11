/**
 * i18n.js — Language config and UI string translations for NyayaMitra.
 * Supports: English, Hindi, Bengali, Marathi, Tamil.
 * No external library needed — plain JS object lookup.
 */

export const LANGUAGES = [
  { code: "en", label: "English",  speechCode: "en-US" },
  { code: "hi", label: "हिंदी",    speechCode: "hi-IN" },
  { code: "bn", label: "বাংলা",    speechCode: "bn-IN" },
  { code: "mr", label: "मराठी",    speechCode: "mr-IN" },
  { code: "ta", label: "தமிழ்",    speechCode: "ta-IN" },
];

export const WELCOME_MESSAGES = {
  en: "Namaste! I'm NyayaMitra. Please describe your situation — what happened, when, where, and who was involved? You can type in any language.",
  hi: "नमस्ते! मैं न्यायमित्र हूँ। कृपया अपनी स्थिति बताइए — क्या हुआ, कब हुआ, कहाँ हुआ, और कौन शामिल था?",
  bn: "নমস্কার! আমি ন্যায়মিত্র। আপনার পরিস্থিতি বর্ণনা করুন — কী হয়েছে, কখন, কোথায় এবং কে জড়িত ছিল?",
  mr: "नमस्कार! मी न्यायमित्र आहे। तुमची परिस्थिती सांगा — काय झाले, केव्हा, कुठे आणि कोण सामील होते?",
  ta: "வணக்கம்! நான் நியாமிதிரா. உங்கள் நிலைமையை விவரிக்கவும் — என்ன நடந்தது, எப்போது, எங்கே, யார் சம்பந்தப்பட்டனர்?",
};

export const STRINGS = {
  en: {
    step_label:        "Step 2 of 3",
    describe_heading:  "Describe your situation",
    describe_subtext:  "Type in Hindi or English — like you're telling a friend",
    placeholder:       "Type your reply... (Hindi ya English dono chalega)",
    send:              "Send",
    proceed:           "Proceed to Drafting",
    try_example:       "Try example",
    skip:              "Skip / Force Proceed",
    info_collected:    "Information collected. Ready to generate your document.",
    starting:          "Starting pipeline...",
    processing_heading:"Generating your document...",
    filing_heading:    "Filing Instructions",
    results_ready:     "Your document is ready",
  },
  hi: {
    step_label:        "चरण 2 / 3",
    describe_heading:  "अपनी स्थिति बताइए",
    describe_subtext:  "हिंदी या English में लिखें — जैसे किसी दोस्त को बताते हैं",
    placeholder:       "यहाँ लिखें...",
    send:              "भेजें",
    proceed:           "दस्तावेज़ बनाएं",
    try_example:       "उदाहरण देखें",
    skip:              "छोड़ें / आगे बढ़ें",
    info_collected:    "जानकारी मिल गई। दस्तावेज़ बनाने के लिए तैयार हैं।",
    starting:          "शुरू हो रहा है...",
    processing_heading:"दस्तावेज़ बन रहा है...",
    filing_heading:    "दाखिल करने के निर्देश",
    results_ready:     "आपका दस्तावेज़ तैयार है",
  },
  bn: {
    step_label:        "ধাপ ২ / ৩",
    describe_heading:  "আপনার পরিস্থিতি বর্ণনা করুন",
    describe_subtext:  "বাংলা বা ইংরেজিতে লিখুন — বন্ধুকে বলার মতো করে",
    placeholder:       "এখানে লিখুন...",
    send:              "পাঠান",
    proceed:           "নথি তৈরি করুন",
    try_example:       "উদাহরণ দেখুন",
    skip:              "এড়িয়ে যান / এগিয়ে যান",
    info_collected:    "তথ্য সংগ্রহ হয়েছে। নথি তৈরির জন্য প্রস্তুত।",
    starting:          "শুরু হচ্ছে...",
    processing_heading:"নথি তৈরি হচ্ছে...",
    filing_heading:    "দাখিল করার নির্দেশনা",
    results_ready:     "আপনার নথি প্রস্তুত",
  },
  mr: {
    step_label:        "पायरी २ / ३",
    describe_heading:  "तुमची परिस्थिती सांगा",
    describe_subtext:  "मराठी किंवा इंग्रजीत लिहा — मित्राला सांगतो तसे",
    placeholder:       "इथे लिहा...",
    send:              "पाठवा",
    proceed:           "कागदपत्र तयार करा",
    try_example:       "उदाहरण पहा",
    skip:              "वगळा / पुढे जा",
    info_collected:    "माहिती गोळा झाली. कागदपत्र तयार करण्यास तयार.",
    starting:          "सुरू होत आहे...",
    processing_heading:"कागदपत्र तयार होत आहे...",
    filing_heading:    "दाखल करण्याच्या सूचना",
    results_ready:     "तुमचे कागदपत्र तयार आहे",
  },
  ta: {
    step_label:        "படி 2 / 3",
    describe_heading:  "உங்கள் நிலைமையை விவரிக்கவும்",
    describe_subtext:  "தமிழ் அல்லது ஆங்கிலத்தில் எழுதுங்கள் — நண்பரிடம் சொல்வது போல்",
    placeholder:       "இங்கே எழுதுங்கள்...",
    send:              "அனுப்பு",
    proceed:           "ஆவணம் உருவாக்கு",
    try_example:       "உதாரணம் பார்க்க",
    skip:              "தவிர்க்க / தொடர்க",
    info_collected:    "தகவல் சேகரிக்கப்பட்டது. ஆவணம் உருவாக்க தயார்.",
    starting:          "தொடங்குகிறது...",
    processing_heading:"ஆவணம் உருவாக்கப்படுகிறது...",
    filing_heading:    "தாக்கல் வழிமுறைகள்",
    results_ready:     "உங்கள் ஆவணம் தயார்",
  },
};
