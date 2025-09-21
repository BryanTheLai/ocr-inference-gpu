'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  page: number;
}

interface PDFViewerProps {
  file: File | string;
  highlights?: Array<{
    box: number[][];
    page_number: number;
    text?: string;
  }>;
  selectedHighlight?: number;
  onHighlightClick?: (index: number) => void;
}

export default function PDFViewer({ 
  file, 
  highlights = [], 
  selectedHighlight,
  onHighlightClick 
}: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [pageWidth, setPageWidth] = useState<number>(0);
  const [pageHeight, setPageHeight] = useState<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const onPageLoadSuccess = ({ width, height }: { width: number; height: number }) => {
    setPageWidth(width);
    setPageHeight(height);
    
    // Auto-fit to container width
    if (containerRef.current) {
      const containerWidth = containerRef.current.clientWidth - 40; // padding
      const newScale = containerWidth / width;
      setScale(Math.min(newScale, 1.5)); // Max scale 1.5
    }
  };

  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setPageNumber(prev => Math.min(prev + 1, numPages));
  };

  const zoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3));
  };

  const zoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5));
  };

  const fitToWidth = () => {
    if (containerRef.current && pageWidth) {
      const containerWidth = containerRef.current.clientWidth - 40;
      setScale(containerWidth / pageWidth);
    }
  };

  const convertBoxToRect = (box: number[][]): BoundingBox | null => {
    if (!box || box.length !== 4) return null;
    
    const xs = box.map(point => point[0]);
    const ys = box.map(point => point[1]);
    
    return {
      x: Math.min(...xs),
      y: Math.min(...ys),
      width: Math.max(...xs) - Math.min(...xs),
      height: Math.max(...ys) - Math.min(...ys),
      page: 1
    };
  };

  const renderHighlights = () => {
    const pageHighlights = highlights.filter(h => h.page_number === pageNumber);
    
    return pageHighlights.map((highlight, index) => {
      const rect = convertBoxToRect(highlight.box);
      if (!rect) return null;
      
      const globalIndex = highlights.indexOf(highlight);
      const isSelected = selectedHighlight === globalIndex;
      
      // Scale coordinates to match current zoom
      const scaledX = (rect.x / pageWidth) * 100;
      const scaledY = (rect.y / pageHeight) * 100;
      const scaledWidth = (rect.width / pageWidth) * 100;
      const scaledHeight = (rect.height / pageHeight) * 100;
      
      return (
        <div
          key={index}
          onClick={() => onHighlightClick && onHighlightClick(globalIndex)}
          className={`absolute border-2 cursor-pointer transition-all ${
            isSelected 
              ? 'border-blue-500 bg-blue-200 bg-opacity-30' 
              : 'border-yellow-400 bg-yellow-200 bg-opacity-20 hover:bg-opacity-30'
          }`}
          style={{
            left: `${scaledX}%`,
            top: `${scaledY}%`,
            width: `${scaledWidth}%`,
            height: `${scaledHeight}%`,
            pointerEvents: 'auto'
          }}
          title={highlight.text || 'Click to select'}
        />
      );
    });
  };

  // Jump to page with selected highlight
  useEffect(() => {
    if (selectedHighlight !== undefined && highlights[selectedHighlight]) {
      const targetPage = highlights[selectedHighlight].page_number;
      if (targetPage !== pageNumber) {
        setPageNumber(targetPage);
      }
    }
  }, [selectedHighlight, highlights]);

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 bg-white border-b">
        <div className="flex items-center space-x-2">
          <button
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          
          <span className="px-3 py-1 bg-gray-100 rounded">
            {pageNumber} / {numPages || '?'}
          </span>
          
          <button
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={zoomOut}
            className="p-2 rounded hover:bg-gray-100"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          
          <span className="px-3 py-1 bg-gray-100 rounded min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          
          <button
            onClick={zoomIn}
            className="p-2 rounded hover:bg-gray-100"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          
          <button
            onClick={fitToWidth}
            className="p-2 rounded hover:bg-gray-100"
          >
            <Maximize2 className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      {/* PDF Content */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto p-4 flex justify-center"
      >
        <div className="relative">
          <Document
            file={file}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              </div>
            }
            error={
              <div className="flex items-center justify-center h-96">
                <p className="text-red-500">Failed to load PDF</p>
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              onLoadSuccess={onPageLoadSuccess}
              renderTextLayer={true}
              renderAnnotationLayer={true}
            />
          </Document>
          
          {/* Highlight Overlay */}
          <div 
            className="absolute top-0 left-0"
            style={{
              width: pageWidth * scale,
              height: pageHeight * scale,
              pointerEvents: 'none'
            }}
          >
            {renderHighlights()}
          </div>
        </div>
      </div>
      
      {/* Highlight Info */}
      {selectedHighlight !== undefined && highlights[selectedHighlight] && (
        <div className="p-3 bg-white border-t">
          <p className="text-sm text-gray-600">Selected text:</p>
          <p className="text-sm font-medium">{highlights[selectedHighlight].text || 'No text available'}</p>
        </div>
      )}
    </div>
  );
}
