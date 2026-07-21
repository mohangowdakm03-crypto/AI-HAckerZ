"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send, Paperclip, Loader2 } from 'lucide-react';

interface ChatInputBarProps {
  isLoading: boolean;
  handleSend: (text: string) => void;
  uploadStatus: string | null;
  onFileUpload: (file: File) => void;
}

export default function ChatInputBar({ isLoading, handleSend, uploadStatus, onFileUpload }: ChatInputBarProps) {
  const [input, setInput] = useState('');
  const recognitionRef = useRef<any>(null);
  const [isListening, setIsListening] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    onFileUpload(file);
    if (fileInputRef.current) {
        fileInputRef.current.value = ''; // reset
    }
  };

  return (
    <div className="p-4 px-6 relative w-full border-t border-white/20">
      <form 
        onSubmit={(e) => {
          e.preventDefault();
          if (input.trim() && !isLoading) {
            handleSend(input);
            setInput('');
          }
        }}
        className="flex gap-3 relative w-full items-end"
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange}
          accept=".txt,.pdf,.json"
          className="hidden"
        />
        
        <button
          type="button"
          className="liquid-btn w-12 h-12 flex-shrink-0 flex items-center justify-center p-0"
          onClick={() => fileInputRef.current?.click()}
          disabled={!!uploadStatus}
          title="Upload Document"
        >
          {uploadStatus ? <Loader2 size={22} className="animate-spin text-cyan-500" /> : <Paperclip size={22} />}
        </button>

        <button 
          type="button"
          className={`liquid-btn w-12 h-12 flex-shrink-0 flex items-center justify-center p-0 ${isListening ? 'text-rose-500' : 'text-inherit'}`}
          onClick={toggleListening}
          title="Voice Input"
        >
          {isListening ? <MicOff size={22} className="pulse" /> : <Mic size={22} />}
        </button>
        
        <div className="liquid-input flex-1 flex items-center px-5 min-h-[48px]">
          <textarea 
            value={input}
            onChange={e => {
              setInput(e.target.value);
              e.target.style.height = '24px';
              e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
            }}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (input.trim() && !isLoading) {
                  handleSend(input);
                  setInput('');
                  e.target.style.height = '24px';
                }
              }
            }}
            placeholder="Ask anything..."
            rows={1}
            className="flex-1 bg-transparent border-none text-inherit text-[1rem] outline-none resize-none min-h-[48px] max-h-[150px] py-[14px] leading-5 overflow-y-auto font-inherit box-border"
          />
        </div>
        
        <button 
          type="submit"
          className={`liquid-btn w-12 h-12 flex-shrink-0 flex items-center justify-center p-0 ${input.trim() ? 'text-cyan-500' : 'text-gray-400'}`}
          disabled={isLoading || !input.trim()}
        >
          <Send size={22} />
        </button>
        
        {uploadStatus && (
          <div className="absolute bottom-[calc(100%+20px)] left-1/2 transform -translate-x-1/2 bg-cyan-600 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-[0_8px_24px_rgba(34,211,238,0.4),0_2px_8px_rgba(0,0,0,0.1)] animate-[fadeUp_0.3s_cubic-bezier(0.4,0,0.2,1)] z-50">
            {uploadStatus}
          </div>
        )}
      </form>
    </div>
  );
}
