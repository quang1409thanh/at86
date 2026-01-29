import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause } from 'lucide-react';
import { cn } from '../lib/utils';
import { STATIC_URL } from '../api/client';

interface AudioPlayerProps {
  src: string;
  className?: string;
  autoplay?: boolean;
}

export default function AudioPlayer({ src, className, autoplay = false }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);

  // Helper to ensure full URL
  const fullSrc = src.startsWith('http') ? src : `${STATIC_URL}/${src}`;

  useEffect(() => {
    if (autoplay && audioRef.current) {
        audioRef.current.play().catch(e => console.log("Autoplay prevented", e));
    }
  }, [src, autoplay]);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const onTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const onLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };
  
  const onEnded = () => {
      setIsPlaying(false);
  }

  const changeSpeed = () => {
    const rates = [0.8, 1, 1.2, 1.5];
    const nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
    const newRate = rates[nextIdx];
    setPlaybackRate(newRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = newRate;
    }
  };

  const formatTime = (time: number) => {
    const min = Math.floor(time / 60);
    const sec = Math.floor(time % 60);
    return `${min}:${sec < 10 ? '0' : ''}${sec}`;
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
      const time = Number(e.target.value);
      if (audioRef.current) {
          audioRef.current.currentTime = time;
          setCurrentTime(time);
      }
  }

  return (
    <div className={cn("bg-white rounded-xl border border-gray-200 p-3 shadow-sm flex items-center gap-3", className)}>
      <audio
        ref={audioRef}
        src={fullSrc}
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={onLoadedMetadata}
        onEnded={onEnded}
      />
      
      <button 
        onClick={togglePlay}
        className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700 transition"
      >
        {isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" className="ml-0.5" />}
      </button>

      <div className="flex-1 flex flex-col gap-1">
          <input 
              type="range"
              min={0}
              max={duration || 0}
              value={currentTime}
              onChange={handleSeek}
              className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex justify-between text-xs text-gray-400 font-mono">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
          </div>
      </div>

      <button onClick={changeSpeed} className="text-xs font-bold text-gray-500 bg-gray-100 px-2 py-1 rounded hover:bg-gray-200 w-12">
          {playbackRate}x
      </button>
    </div>
  );
}
