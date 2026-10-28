import React, { useState, useRef, useEffect } from 'react';
import { chatWithData } from '../api';
import { Send, User, Bot, BarChart2 } from 'lucide-react';

const AIAnalyst = ({ datasetId }) => {
    const [messages, setMessages] = useState([
        { role: 'bot', content: "Hi! I'm your AI Data Analyst. Ask me about your data (e.g., 'Show me the average revenue', 'Plot sales by region')." }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || !datasetId) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const response = await chatWithData(datasetId, userMsg.content);

            const botMsg = {
                role: 'bot',
                content: response.content,
                type: response.type,
                imageData: response.image_data,
                html: response.html
            };

            setMessages(prev => [...prev, botMsg]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'bot', content: "Sorry, I encountered an error analyzing your request." }]);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
            {/* Header */}
            <div className="bg-slate-800 p-4 border-b border-slate-700 flex items-center gap-2">
                <Bot className="text-blue-400" size={24} />
                <h2 className="text-lg font-semibold text-white">AI Analyst</h2>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg p-3 ${msg.role === 'user'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-700 text-slate-200'
                            }`}>
                            {/* Text Content */}
                            <div className="whitespace-pre-wrap">{msg.content}</div>

                            {/* HTML/Table Content */}
                            {msg.html && (
                                <div className="mt-2 overflow-x-auto bg-slate-800 rounded p-2"
                                    dangerouslySetInnerHTML={{ __html: msg.content }} />
                            )}

                            {/* Image Content */}
                            {msg.type === 'plot' && msg.imageData && (
                                <div className="mt-2 bg-white rounded p-1">
                                    <img src={`data:image/png;base64,${msg.imageData}`} alt="Data Plot" className="w-full rounded" />
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-700 text-slate-400 rounded-lg p-3 italic">
                            Thinking...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 bg-slate-800 border-t border-slate-700 flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask a question about your data..."
                    className="flex-1 bg-slate-900 text-white border border-slate-600 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
                    disabled={loading}
                />
                <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg disabled:opacity-50 transition-colors"
                >
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
};

export default AIAnalyst;
