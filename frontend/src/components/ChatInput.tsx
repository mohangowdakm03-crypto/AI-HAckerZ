"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Paperclip, Mic, MicOff } from 'lucide-react';

interface ChatInputProps {
  isLoading: boolean;
  isUploading: boolean;
  uploadStatus: string | null;
  onSend: (text: string) => void;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export default function ChatInput({
  isLoading,
  isUploading,
  uploadStatus,
  onSend,
  onFileUpload,
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false;
        recognitionRef.current.lang = 'en-US';

        recognitionRef.current.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInput((prev) => prev + (prev ? ' ' : '') + transcript);
          setIsListening(false);
        };

        recognitionRef.current.onerror = (event: any) => {
          console.error("Speech recognition error", event.error);
          setIsListening(false);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    onSend(input);
    setInput('');
  };

  return (
    <div className="px-6 py-4">
      <form onSubmit={handleSend} className="w-full relative max-w-2xl mx-auto px-4">
        <div className="flex items-center justify-center gap-6 w-full">
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={onFileUpload}
          accept=".txt,.pdf,.json"
          className="hidden" 
        />
        <button
          type="button"
          className="apple-convex-button w-20 h-20 flex-shrink-0 flex items-center justify-center p-0"
          onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            title="Upload Document"
          >
            {isUploading ? <Loader2 size={24} className="animate-spin" /> : <Paperclip size={24} />}
          </button>
          
        <button
          type="button"
          className={`apple-convex-button w-20 h-20 flex-shrink-0 flex items-center justify-center p-0 ${isListening ? 'text-rose-500' : 'text-inherit'}`}
          onClick={toggleListening}
            title="Voice Input"
          >
            {isListening ? <MicOff size={24} className="pulse" /> : <Mic size={24} />}
          </button>
          
        <div className="apple-glass-pill flex-1 flex items-center px-6 min-h-[36px]">
          <textarea 
              value={input}
              onChange={e => {
                setInput(e.target.value);
                const target = e.target as HTMLTextAreaElement;
                target.style.height = '24px';
                target.style.height = Math.min(target.scrollHeight, 150) + 'px';
              }}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (input.trim() && !isLoading) {
                    handleSend();
                    (e.target as HTMLTextAreaElement).style.height = '24px';
                  }
                }
              }}
              placeholder="Ask anything..."
              rows={1}
            className="flex-1 bg-transparent border-none text-inherit text-sm outline-none resize-none font-inherit box-border min-h-[36px] max-h-[150px] py-[8px] leading-5 overflow-y-auto"
          />
        </div>
        
          <button 
            type="submit"
            className={`apple-convex-button w-20 h-20 flex-shrink-0 flex items-center justify-center p-0 ${input.trim() ? 'text-cyan-500' : 'text-slate-500'}`}
            disabled={isLoading || !input.trim()}
          >
            <Send size={24} />
          </button>
        </div>
      </form>
      
      {uploadStatus && (
        <div className="absolute bottom-[calc(100%+20px)] left-1/2 -translate-x-1/2 bg-cyan-500 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-[0_8px_24px_rgba(34,211,238,0.4),0_2px_8px_rgba(0,0,0,0.1)] animate-[fadeUp_0.3s_cubic-bezier(0.4,0,0.2,1)] z-50">
          {uploadStatus}
        </div>
      )}
    </div>
  );
}
