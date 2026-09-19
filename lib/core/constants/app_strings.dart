/// Centralized string constants for the NHAA Stress Assessment application.
///
/// All user-facing strings should be defined here to support
/// future localization and consistent labeling across the app.
class AppStrings {
  AppStrings._();

  // ── Active Locale ───────────────────────────────────────────────
  static String _currentLanguageCode = 'en';
  static String get currentLanguageCode => _currentLanguageCode;

  static void setLocale(String code) {
    final lower = code.toLowerCase();
    if (lower.startsWith('ta')) {
      _currentLanguageCode = 'ta';
    } else if (lower.startsWith('hi')) {
      _currentLanguageCode = 'hi';
    } else if (lower.startsWith('te')) {
      _currentLanguageCode = 'te';
    } else if (lower.startsWith('kn') || lower.startsWith('ka')) {
      _currentLanguageCode = 'kn';
    } else if (lower.startsWith('ml') || lower.startsWith('ma')) {
      _currentLanguageCode = 'ml';
    } else {
      _currentLanguageCode = 'en';
    }
  }

  // ── Verified Emergency / Support Contact Numbers ───
  /// Nationwide verified emergency helpline numbers in India.
  static const String emergencyContactNumber = '112';
  static const String womenHelplineNumber = '181';
  static const String demoContactNumber = '112'; // Backwards-compatible alias to 112
  static const String demoSupportLabel = 'National Emergency (112)';
  static const String demoEmergencyLabel = 'Women Helpline (181)';
  static const String demoDisclaimer =
      'For nationwide emergency assistance across India, dial 112 for immediate police, fire, or ambulance dispatch, or 181 for women support services.';

  // ── App Identity ────────────────────────────────────────────────
  static const String appName = 'TrueVoice';
  static const String appFullName =
      'AI-Based Real-Time Stress and Trauma Assessment';
  static const String appTagline = 'Your voice matters.';
  static const String organizationName =
      'National Helpline Against Atrocities';

  // ── Victim Flow Titles ──────────────────────────────────────────
  static const String splashTitle = 'TrueVoice';
  static const String welcomeTitle = 'Welcome';
  static const String languageSelectionTitle = 'Choose Your Language';
  static const String consentTitle = 'Consent & Privacy';
  static const String homeTitle = 'Home';
  static const String aiChatTitle = 'Talk to Us';
  static const String voiceInteractionTitle = 'Voice Support';
  static const String assessmentStatusTitle = 'Assessment Status';
  static const String supportEmergencyTitle = 'Support & Emergency';

  // ── Responder Flow Titles ───────────────────────────────────────
  static const String loginTitle = 'Responder Login';
  static const String dashboardTitle = 'Dashboard';
  static const String caseListTitle = 'Cases';
  static const String caseDetailsTitle = 'Case Details';
  static const String aiAssessmentTitle = 'AI Assessment';
  static const String sviRiskTitle = 'SVI / Risk Details';
  static const String recommendedInterventionTitle =
      'Recommended Intervention';
  static const String caseHistoryTitle = 'Case History';

  // ── Common ─────────────────────────────────────────────────────
  static const String continueText = 'Continue';
  static const String backText = 'Back';
  static const String cancelText = 'Cancel';
  static const String confirmText = 'Confirm';
  static const String submitText = 'Submit';
  static const String loadingText = 'Loading...';
  static const String errorText = 'Something went wrong';
  static const String retryText = 'Retry';

  // ── Multilingual Localization Translations ──────────────────────
  static final Map<String, Map<String, String>> _translations = {
    // English
    'en': {
      'sanctuary_home': 'TrueVoice Home',
      'nhaa_sanctuary': 'TrueVoice Sanctuary',
      'safe_encrypted': 'Encrypted, safe & confidential',
      'how_share': 'How would you like to share what happened?',
      'choose_pace': 'Choose the way that feels most comfortable for you.',
      'talk_with_us': 'Talk with us',
      'talk_subtitle': 'Share using your voice in your comfortable language',
      'type_it_out': 'Type it out',
      'type_subtitle': 'Write your thoughts privately through text chat',
      'support_pathways': 'Support Pathways',
      'crisis_banner_title': 'Feeling unsafe right now?',
      'crisis_banner_sub': 'Connect to emergency helpline immediately',
      'demo_call': 'Emergency Call (112)',
      'demo_support': 'National Emergency (112)',
      'demo_line': 'Women Helpline (181)',
      'chat_title': 'Sanctuary Guide',
      'chat_hint': 'Type your thoughts here at your own pace...',
      'chat_listening': 'Listening gently... Take your time.',
      'send': 'Send',
      'breathe': 'Breathe',
      'voice_title': 'Voice Support',
      'tap_to_speak': 'Tap to speak',
      'listening': 'Listening...',
      'stop_process': 'Stop & Process',
      'transcribing': 'Processing voice with AI...',
      'welcome_heading': 'You are in a safe, confidential space.',
      'welcome_subheading': 'AI-assisted trauma & stress support designed to guide you with care and dignity.',
      'start_journey': 'Begin Safe Intake',
      'confirm_continue': 'Confirm & Continue',
      'private_safe': 'Private & safe',
    },
    // Tamil (தமிழ்)
    'ta': {
      'sanctuary_home': 'பாதுகாப்பு இல்லம்',
      'nhaa_sanctuary': 'NHAA சரணாலயம்',
      'safe_encrypted': 'மறைமுகமானது, பாதுகாப்பானது',
      'how_share': 'எவ்வாறு பகிர விரும்புகிறீர்கள்?',
      'choose_pace': 'உங்களுக்கு மிகவும் வசதியான வழியைத் தேர்ந்தெடுங்கள்.',
      'talk_with_us': 'எங்களுடன் பேசுங்கள்',
      'talk_subtitle': 'உங்கள் தாய்மொழியில் வாய்ஸ் மூலம் பேசுங்கள்',
      'type_it_out': 'எழுதிப் பகிருங்கள்',
      'type_subtitle': 'உரையாடல் மூலம் அமைதியாக உங்கள் எண்ணங்களை எழுதுங்கள்',
      'support_pathways': 'ஆதரவு சேவைகள்',
      'crisis_banner_title': 'பாதுகாப்பற்றதாக உணர்கிறீர்களா?',
      'crisis_banner_sub': 'அவசர உதவி எண்ணை உடனே தொடர்பு கொள்ளுங்கள்',
      'demo_call': 'அவசர அழைப்பு (112)',
      'demo_support': 'தேசிய அவசர உதவி (112)',
      'demo_line': 'மகளிர் உதவி எண் (181)',
      'chat_title': 'உதவி வழிகாட்டி',
      'chat_hint': 'உங்கள் எண்ணங்களை உங்கள் சொந்த வேகத்தில் எழுதுங்கள்...',
      'chat_listening': 'கவனமாகக் கேட்கிறது... நிதானமாகப் பேசுங்கள்.',
      'send': 'அனுப்புக',
      'breathe': 'சுவாசம்',
      'voice_title': 'குரல் ஆதரவு',
      'tap_to_speak': 'பேச தட்டவும்',
      'listening': 'கேட்கிறது...',
      'stop_process': 'நிறுத்தி செயலாக்கு',
      'transcribing': 'குரல் செயலாக்கப்படுகிறது...',
      'welcome_heading': 'நீங்கள் ஒரு பாதுகாப்பான இடத்தில் இருக்கிறீர்கள்.',
      'welcome_subheading': 'கவலையற்ற, கண்ணியமான ஆதரவை வழங்க AI வழிகாட்டி தயாராக உள்ளது.',
      'start_journey': 'தொடங்கவும்',
      'confirm_continue': 'உறுதிசெய்து தொடர்க',
      'private_safe': 'தனிப்பட்டது & பாதுகாப்பானது',
    },
    // Hindi (हिन्दी)
    'hi': {
      'sanctuary_home': 'सुरक्षित आश्रय',
      'nhaa_sanctuary': 'NHAA आश्रय',
      'safe_encrypted': 'एन्क्रिप्टेड, सुरक्षित एवं गोपनीय',
      'how_share': 'आप कैसे साझा करना चाहेंगे?',
      'choose_pace': 'वह विकल्प चुनें जो आपके लिए सबसे सहज हो।',
      'talk_with_us': 'हमसे बात करें',
      'talk_subtitle': 'अपनी सहज भाषा में बोलकर साझा करें',
      'type_it_out': 'लिखकर बताएं',
      'type_subtitle': 'टेक्स्ट चैट के माध्यम से अपने विचार लिखें',
      'support_pathways': 'सहायता विकल्प',
      'crisis_banner_title': 'क्या आप असुरक्षित महसूस कर रहे हैं?',
      'crisis_banner_sub': 'आपातकालीन हेल्पलाइन से तुरंत संपर्क करें',
      'demo_call': 'आपातकालीन कॉल (112)',
      'demo_support': 'राष्ट्रीय आपातकालीन (112)',
      'demo_line': 'महिला हेल्पलाइन (181)',
      'chat_title': 'सहायता मार्गदर्शक',
      'chat_hint': 'अपनी गति से यहां अपने विचार लिखें...',
      'chat_listening': 'ध्यान से सुन रहे हैं... आराम से बोलें।',
      'send': 'भेजें',
      'breathe': 'श्वास लें',
      'voice_title': 'आवाज सहायता',
      'tap_to_speak': 'बोलने के लिए टैप करें',
      'listening': 'सुन रहे हैं...',
      'stop_process': 'रोकें और संसाधित करें',
      'transcribing': 'आवाज का विश्लेषण हो रहा है...',
      'welcome_heading': 'आप एक सुरक्षित और गोपनीय स्थान पर हैं।',
      'welcome_subheading': 'सम्मान और संवेदनशीलता के साथ आपकी सहायता के लिए तैयार।',
      'start_journey': 'प्रारंभ करें',
      'confirm_continue': 'पुष्टि करें और आगे बढ़ें',
      'private_safe': 'निजी और सुरक्षित',
    },
    // Telugu (తెలుగు)
    'te': {
      'sanctuary_home': 'సురక్షిత కేంద్రం',
      'nhaa_sanctuary': 'NHAA ఆశ్రయం',
      'safe_encrypted': 'రక్షితం మరియు సురక్షితం',
      'how_share': 'మీరు ఎలా పంచుకోవాలనుకుంటున్నారు?',
      'choose_pace': 'మీకు అనుకూలమైన విధానాన్ని ఎంచుకోండి.',
      'talk_with_us': 'మాతో మాట్లాడండి',
      'talk_subtitle': 'మీ సౌకర్యవంతమైన భాషలో మాట్లాడండి',
      'type_it_out': 'టైప్ చేయండి',
      'type_subtitle': 'టెక్స్ట్ చాట్ ద్వారా మీ భావాలను పంచుకోండి',
      'support_pathways': 'మద్దతు మార్గాలు',
      'crisis_banner_title': 'అభద్రతా భావనగా ఉందా?',
      'crisis_banner_sub': 'అత్యవసర హెల్ప్‌లైన్‌ను వెంటనే సంప్రదించండి',
      'demo_call': 'అత్యవసర కాల్ (112)',
      'demo_support': 'జాతీయ అత్యవసర సహాయం (112)',
      'demo_line': 'మహిళా హెల్ప్‌లైన్ (181)',
      'chat_title': 'గైడ్',
      'chat_hint': 'మీ ఆలోచనలను ఇక్కడ టైప్ చేయండి...',
      'chat_listening': 'వింటున్నాము... సమయం తీసుకోండి.',
      'send': 'పంపు',
      'breathe': 'శ్వాస తీసుకోండి',
      'voice_title': 'వాయిస్ మద్దతు',
      'tap_to_speak': 'మాట్లాడటానికి నొక్కండి',
      'listening': 'వింటున్నాము...',
      'stop_process': 'ఆపి విశ్లేషించండి',
      'transcribing': 'వాయిస్ విశ్లేషించబడుతోంది...',
      'welcome_heading': 'మీరు సురక్షితమైన ప్రదేశంలో ఉన్నారు.',
      'welcome_subheading': 'మీకు గౌరవప్రదమైన మద్దతు అందించడానికి సిద్ధంగా ఉన్నాము.',
      'start_journey': 'ప్రారంభించండి',
      'confirm_continue': 'ధృవీకరించి కొనసాగండి',
      'private_safe': 'వ్యక్తిగతం & సురక్షితం',
    },
    // Kannada (ಕನ್ನಡ)
    'kn': {
      'sanctuary_home': 'ಸುರಕ್ಷಿತ ಆಶ್ರಯ',
      'nhaa_sanctuary': 'NHAA ಆಶ್ರಯ',
      'safe_encrypted': 'ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾದ, ಸುರಕ್ಷಿತ',
      'how_share': 'ನೀವು ಹೇಗೆ ಹಂಚಿಕೊಳ್ಳಲು ಬಯಸುತ್ತೀರಿ?',
      'choose_pace': 'ನಿಮಗೆ ಹೆಚ್ಚು ಆರಾಮದಾಯಕವಾದ ಆಯ್ಕೆಯನ್ನು ಆರಿಸಿ.',
      'talk_with_us': 'ನಮ್ಮೊಂದಿಗೆ ಮಾತನಾಡಿ',
      'talk_subtitle': 'ನಿಮ್ಮ ಆರಾಮದಾಯಕ ಭಾಷೆಯಲ್ಲಿ ಮಾತನಾಡಿ',
      'type_it_out': 'ಬರೆದು ತಿಳಿಸಿ',
      'type_subtitle': 'ಟೆಕ್ಸ್ಟ್ ಚಾಟ್ ಮೂಲಕ ನಿಮ್ಮ ಆಲೋಚನೆಗಳನ್ನು ಹಂಚಿಕೊಳ್ಳಿ',
      'support_pathways': 'ಬೆಂಬಲ ಮಾರ್ಗಗಳು',
      'crisis_banner_title': 'ಅಸುರಕ್ಷಿತ ಭಾವನೆ ಇದೆಯೇ?',
      'crisis_banner_sub': 'ತುರ್ತು ಸಹಾಯವಾಣಿಯನ್ನು ತಕ್ಷಣ ಸಂಪರ್ಕಿಸಿ',
      'demo_call': 'ತುರ್ತು ಕರೆ (112)',
      'demo_support': 'ರಾಷ್ಟ್ರೀಯ ತುರ್ತು ಸಹಾಯ (112)',
      'demo_line': 'ಮಹಿಳಾ ಸಹಾಯವಾಣಿ (181)',
      'chat_title': 'ಮಾರ್ಗದರ್ಶಿ',
      'chat_hint': 'ನಿಮ್ಮ ಆಲೋಚನೆಗಳನ್ನು ಇಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ...',
      'chat_listening': 'ಗಮನವಿಟ್ಟು ಆಲಿಸುತ್ತಿದ್ದೇವೆ...',
      'send': 'ಕಳುಹಿಸಿ',
      'breathe': 'ಉಸಿರಾಡಿ',
      'voice_title': 'ಧ್ವನಿ ಬೆಂಬಲ',
      'tap_to_speak': 'ಮಾತನಾಡಲು ಟ್ಯಾಪ್ ಮಾಡಿ',
      'listening': 'ಆಲಿಸಲಾಗುತ್ತಿದೆ...',
      'stop_process': 'ನಿಲ್ಲಿಸಿ ಮತ್ತು ವಿಶ್ಲೇಷಿಸಿ',
      'transcribing': 'ಧ್ವನಿಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...',
      'welcome_heading': 'ನೀವು ಸುರಕ್ಷಿತ ಜಾಗದಲ್ಲಿದ್ದೀರಿ.',
      'welcome_subheading': 'ಗೌರವ ಮತ್ತು ಕಾಳಜಿಯೊಂದಿಗೆ ನಿಮ್ಮನ್ನು ಬೆಂಬಲಿಸಲು ಸಿದ್ಧ.',
      'start_journey': 'ಪ್ರಾರಂಭಿಸಿ',
      'confirm_continue': 'ದೃಢೀಕರಿಸಿ ಮತ್ತು ಮುಂದುವರಿಯಿರಿ',
      'private_safe': 'ಖಾಸಗಿ ಮತ್ತು ಸುರಕ್ಷಿತ',
    },
    // Malayalam (മലയാളം)
    'ml': {
      'sanctuary_home': 'സുരക്ഷിത കേന്ദ്രം',
      'nhaa_sanctuary': 'NHAA സംരക്ഷണം',
      'safe_encrypted': 'എൻക്രിപ്റ്റ് ചെയ്തതും സുരക്ഷിതവുമായ ഇടം',
      'how_share': 'നിങ്ങൾക്ക് എങ്ങനെ പങ്കുവെക്കാൻ ആഗ്രഹമുണ്ട്?',
      'choose_pace': 'നിങ്ങൾക്ക് ഏറ്റവും അനുയോജ്യമായ മാർഗ്ഗം തിരഞ്ഞെടുക്കുക.',
      'talk_with_us': 'ഞങ്ങളോട് സംസാരിക്കൂ',
      'talk_subtitle': 'നിങ്ങളുടെ ഭാഷയിൽ സംസാരിക്കൂ',
      'type_it_out': 'എഴുതി പങ്കുവെക്കൂ',
      'type_subtitle': 'മെസ്സേജ് ചാറ്റിലൂടെ നിങ്ങളുടെ ചിന്തകൾ പങ്കുവെക്കൂ',
      'support_pathways': 'സഹായ മാർഗ്ഗങ്ങൾ',
      'crisis_banner_title': 'അരക്ഷിതാവസ്ഥ തോന്നുന്നുണ്ടോ?',
      'crisis_banner_sub': 'അടിയന്തര ഹെൽപ്പ് ലൈനുമായി ഉടൻ ബന്ധപ്പെടൂ',
      'demo_call': 'അടിയന്തര കോൾ (112)',
      'demo_support': 'ദേശീയ അടിയന്തര സഹായം (112)',
      'demo_line': 'വനിതാ ഹെൽപ്പ് ലൈൻ (181)',
      'chat_title': 'വഴികാട്ടി',
      'chat_hint': 'നിങ്ങളുടെ ചിന്തകൾ ഇവിടെ ടൈപ്പ് ചെയ്യുക...',
      'chat_listening': 'ശ്രദ്ധാപൂർവ്വം കേൾക്കുന്നു... സാവധാനം സംസാരിക്കൂ.',
      'send': 'അയക്കുക',
      'breathe': 'ശ്വസിക്കുക',
      'voice_title': 'ശബ്ദ സഹായം',
      'tap_to_speak': 'സംസാരിക്കാൻ ടാപ്പ് ചെയ്യുക',
      'listening': 'കേൾക്കുന്നു...',
      'stop_process': 'നിർത്തുക, പരിശോധിക്കുക',
      'transcribing': 'ശബ്ദം പരിശോധിക്കുന്നു...',
      'welcome_heading': 'നിങ്ങൾ സുരക്ഷിതമായ ഒരു ഇടത്തിലാണ്.',
      'welcome_subheading': 'ആദരവോടും കരുതലോടും നിങ്ങളെ സഹായിക്കാൻ ഞങ്ങൾ തയ്യാറാണ്.',
      'start_journey': 'തുടങ്ങുക',
      'confirm_continue': 'സ്ഥിരീകരിച്ച് മുന്നോട്ട് പോവുക',
      'private_safe': 'സ്വകാര്യവും സുരക്ഷിതവും',
    },
  };

  /// Retrieve localized string for the current active language code.
  static String tr(String key, [String? langCode]) {
    final code = langCode ?? _currentLanguageCode;
    final map = _translations[code] ?? _translations['en']!;
    return map[key] ?? _translations['en']?[key] ?? key;
  }
}
