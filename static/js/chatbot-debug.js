// Simple debug test for ChatBot
console.log('🔍 Debug script loaded');

// Check if ChatBot class exists
console.log('ChatBot class type:', typeof ChatBot);
console.log('ChatBot constructor:', ChatBot);

// Try to create instance
try {
    const testBot = new ChatBot();
    console.log('✅ ChatBot instance created:', testBot);
    console.log('✅ ChatBot.init type:', typeof testBot.init);
} catch (error) {
    console.error('❌ Error creating ChatBot:', error);
}

// Check global window.ChatBot
console.log('window.ChatBot type:', typeof window.ChatBot);
console.log('window.ChatBot:', window.ChatBot);

// Test if init method exists
if (window.ChatBot && typeof window.ChatBot.init === 'function') {
    console.log('✅ window.ChatBot.init is available');
} else {
    console.error('❌ window.ChatBot.init is not available');
    console.log('Available methods:', Object.getOwnPropertyNames(window.ChatBot || {}));
}