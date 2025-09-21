'use client';

import React, { useState, useEffect } from 'react';
import FileUpload from '@/components/FileUpload';
import SchemaBuilder from '@/components/SchemaBuilder';
import DataTable from '@/components/DataTable';
import PDFViewer from '@/components/PDFViewer';
import { documentAPI, ExtractionSchema, ExtractionResult } from '@/lib/api';
import { FileText, Settings, Database, Eye, Loader2, CheckCircle, XCircle } from 'lucide-react';

interface ProcessedDocument {
  filename: string;
  file: File;
  result?: ExtractionResult;
  status: 'pending' | 'processing' | 'success' | 'error';
  error?: string;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<'parse' | 'extract' | 'config' | 'result'>('parse');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [processedDocuments, setProcessedDocuments] = useState<ProcessedDocument[]>([]);
  const [currentSchema, setCurrentSchema] = useState<any>({});
  const [documentType, setDocumentType] = useState<string>('invoice');
  const [templates, setTemplates] = useState<Record<string, any>>({});
  const [extractedData, setExtractedData] = useState<any[]>([]);
  const [selectedRow, setSelectedRow] = useState<number>();
  const [selectedDocument, setSelectedDocument] = useState<ProcessedDocument | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [customPrompt, setCustomPrompt] = useState<string>('');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const templatesData = await documentAPI.getTemplates();
      setTemplates(templatesData);
      if (templatesData.invoice) {
        setCurrentSchema(templatesData.invoice.schema);
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleFilesSelected = (files: File[]) => {
    setSelectedFiles(files);
    const newDocs = files.map(file => ({
      filename: file.name,
      file,
      status: 'pending' as const
    }));
    setProcessedDocuments(newDocs);
  };

  const processDocuments = async () => {
    if (selectedFiles.length === 0 || !currentSchema) {
      alert('Please select files and configure a schema');
      return;
    }

    setIsProcessing(true);
    setActiveTab('result');

    const schemaData: ExtractionSchema = {
      schema: currentSchema,
      document_type: documentType,
      extraction_prompt: customPrompt || undefined
    };

    const updatedDocs = [...processedDocuments];
    const allExtractedData: any[] = [];

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      updatedDocs[i].status = 'processing';
      setProcessedDocuments([...updatedDocs]);

      try {
        const result = await documentAPI.processWithSchema(file, schemaData);
        updatedDocs[i].result = result;
        updatedDocs[i].status = 'success';
        
        if (result.extracted_data) {
          allExtractedData.push({
            _source_file: file.name,
            ...result.extracted_data
          });
        }
      } catch (error: any) {
        updatedDocs[i].status = 'error';
        updatedDocs[i].error = error.message || 'Processing failed';
      }

      setProcessedDocuments([...updatedDocs]);
    }

    setExtractedData(allExtractedData);
    setIsProcessing(false);
  };

  const handleRowClick = (row: any, index: number) => {
    setSelectedRow(index);
    const sourceFile = row._source_file;
    const doc = processedDocuments.find(d => d.filename === sourceFile);
    setSelectedDocument(doc || null);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold text-gray-800">Document Processor</h1>
          <p className="text-sm text-gray-600 mt-1">OCR + AI Data Extraction</p>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('parse')}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'parse' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <FileText className="w-4 h-4 inline mr-1" />
            Parse
          </button>
          <button
            onClick={() => setActiveTab('extract')}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'extract' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Database className="w-4 h-4 inline mr-1" />
            Extract
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'config' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Settings className="w-4 h-4 inline mr-1" />
            Config
          </button>
          <button
            onClick={() => setActiveTab('result')}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'result' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Eye className="w-4 h-4 inline mr-1" />
            Result
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-auto p-4">
          {activeTab === 'parse' && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Upload Documents</h2>
              <FileUpload onFilesSelected={handleFilesSelected} />
              
              {processedDocuments.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Processing Status</h3>
                  <div className="space-y-2">
                    {processedDocuments.map((doc, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm truncate flex-1">{doc.filename}</span>
                        {getStatusIcon(doc.status)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'extract' && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Extraction Settings</h2>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type
                </label>
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="invoice">Invoice</option>
                  <option value="medical_form">Medical Form</option>
                  <option value="bank_statement">Bank Statement</option>
                  <option value="contract">Contract</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Custom Extraction Prompt (Optional)
                </label>
                <textarea
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Enter custom instructions for data extraction..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg h-32 resize-none"
                />
              </div>

              <button
                onClick={processDocuments}
                disabled={isProcessing || selectedFiles.length === 0}
                className="w-full py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Process Documents'
                )}
              </button>
            </div>
          )}

          {activeTab === 'config' && (
            <div className="h-full">
              <h2 className="text-lg font-semibold mb-4">Schema Configuration</h2>
              <div className="h-[calc(100%-3rem)]">
                <SchemaBuilder
                  initialSchema={currentSchema}
                  onSchemaChange={setCurrentSchema}
                  templates={templates}
                />
              </div>
            </div>
          )}

          {activeTab === 'result' && (
            <div>
              <h2 className="text-lg font-semibold mb-4">Extraction Results</h2>
              {extractedData.length > 0 ? (
                <div className="text-sm text-gray-600">
                  <p>{extractedData.length} documents processed</p>
                  <p className="mt-2">Click on a row to view the source document</p>
                </div>
              ) : (
                <p className="text-gray-500">No results yet. Process documents to see results.</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex">
        {/* Data Table */}
        <div className="flex-1 p-6 overflow-auto">
          {activeTab === 'result' && extractedData.length > 0 ? (
            <DataTable
              data={extractedData}
              onRowClick={handleRowClick}
              selectedRow={selectedRow}
              title="Extracted Data"
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">Process documents to view extracted data</p>
              </div>
            </div>
          )}
        </div>

        {/* PDF Viewer */}
        {selectedDocument && selectedDocument.file && (
          <div className="w-1/2 border-l border-gray-200">
            <PDFViewer
              file={selectedDocument.file}
              highlights={selectedDocument.result?.ocr_detections}
              selectedHighlight={selectedRow}
            />
          </div>
        )}
      </div>
    </div>
  );
}
