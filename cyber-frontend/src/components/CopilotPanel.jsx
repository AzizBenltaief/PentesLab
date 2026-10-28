import React, { useState, useEffect, useRef } from 'react';
import { scanAPI } from '../services/api';
import Markdown from './Markdown';
import {
  Sparkles, Send, Loader2, AlertCircle, RefreshCw,
  Lightbulb, MessageSquare, FileSearch, ChevronDown
} from 'lucide-react';

const SUGGESTIONS = [
  'What are the top risks?',
  'What should I patch first?',
  'Explain the OpenVAS findings',
  'What would you test next?',
];

const CopilotPanel = ({ scanId }) => {
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [showAnalysis, setShowAnalysis] = useState(false);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState('');
  const [historyOpen, setHistoryOpen] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Restore persisted conversation
    scanAPI.getChatHistory(scanId)
      .then((res) => setMessages(res.data.messages || []))
      .catch(() => {});
  }, [scanId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const getErrorMessage = (err, fallback) => {
    const detail = err?.response?.data?.detail;
    return typeof detail === 'string' ? detail : fallback;
  };

  const generateAnalysis = async (force = false) => {
    setAnalysisLoading(true);
    setAnalysisError('');
    setShowAnalysis(true);
    try {
      const res = await scanAPI.getAnalysis(scanId, force);
      setAnalysis(res.data.analysis);
    } catch (err) {
      setAnalysisError(getErrorMessage(err, 'Failed to generate AI analysis'));
    } finally {
      setAnalysisLoading(false);
    }
  };

  const sendMessage = async (question) => {
    const q = (question ?? input).trim();
    if (!q || sending) return;

    const userMessage = { role: 'user', content: q };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setSending(true);
    setChatError('');

    try {
      // Send conversation history (without timestamps) for context
      const history = messages.map(({ role, content }) => ({ role, content }));
      const res = await scanAPI.chat(scanId, { question: q, history });
      setMessages([...newMessages, { role: 'assistant', content: res.data.answer }]);
    } catch (err) {
      setChatError(getErrorMessage(err, 'Failed to get a response from the copilot'));
      // Remove the optimistic user message so the user can retry
      setMessages(messages);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Sparkles className="h-5 w-5 text-indigo-600" />
            <h3 className="ml-2 text-lg font-medium text-gray-900">AI Security Copilot</h3>
          </div>
          <button
            onClick={() => setShowAnalysis(!showAnalysis)}
            className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center"
          >
            <ChevronDown className={`h-4 w-4 mr-1 transition-transform ${showAnalysis ? 'rotate-180' : ''}`} />
            {showAnalysis ? 'Hide analysis' : 'Show analysis'}
          </button>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          Ask questions about this scan's findings, get prioritized remediation advice.
        </p>
      </div>

      {/* AI Analysis section */}
      {showAnalysis && (
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          {analysisLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 text-indigo-600 animate-spin" />
              <span className="ml-3 text-sm text-gray-600">Analyzing scan results...</span>
            </div>
          ) : analysisError ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
              <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3 flex-1">
                <p className="text-sm text-red-700">{analysisError}</p>
                <button
                  onClick={() => generateAnalysis()}
                  className="mt-2 text-sm text-red-600 hover:text-red-800 font-medium flex items-center"
                >
                  <RefreshCw className="h-3.5 w-3.5 mr-1" /> Retry
                </button>
              </div>
            </div>
          ) : analysis ? (
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center text-sm font-medium text-gray-700">
                  <FileSearch className="h-4 w-4 mr-2 text-indigo-600" />
                  Triage Analysis
                </div>
                <button
                  onClick={() => generateAnalysis(true)}
                  className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center"
                  title="Regenerate analysis"
                >
                  <RefreshCw className="h-3.5 w-3.5 mr-1" /> Regenerate
                </button>
              </div>
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <Markdown>{analysis}</Markdown>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <Lightbulb className="h-8 w-8 text-indigo-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-3">
                Generate an AI-powered triage of this scan: key findings, attack paths and
                prioritized remediation.
              </p>
              <button
                onClick={() => generateAnalysis()}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                Generate AI Analysis
              </button>
            </div>
          )}
        </div>
      )}

      {/* Chat section */}
      <div className="px-6 py-4">
        <div className="flex items-center text-sm font-medium text-gray-700 mb-3">
          <MessageSquare className="h-4 w-4 mr-2 text-indigo-600" />
          Ask the Copilot
        </div>

        {messages.length === 0 && !sending && (
          <div className="flex flex-wrap gap-2 mb-4">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => sendMessage(s)}
                className="text-xs px-3 py-1.5 rounded-full border border-indigo-200 text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.length > 0 && (
          <div className="max-h-96 overflow-y-auto mb-4 space-y-3 pr-1">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-800 border border-gray-200'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div><Markdown>{msg.content}</Markdown></div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 border border-gray-200 rounded-lg px-4 py-3 flex items-center">
                  <Loader2 className="h-4 w-4 text-indigo-600 animate-spin mr-2" />
                  <span className="text-sm text-gray-600">Copilot is thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {chatError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start mb-3">
            <AlertCircle className="h-4 w-4 text-red-400 mt-0.5" />
            <p className="ml-2 text-sm text-red-700 flex-1">{chatError}</p>
          </div>
        )}

        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="e.g. What should I fix first?"
            disabled={sending}
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
          />
          <button
            onClick={() => sendMessage()}
            disabled={sending || !input.trim()}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-400">
          Answers are generated from this scan's data only. Verify critical findings manually.
        </p>
      </div>
    </div>
  );
};

export default CopilotPanel;
