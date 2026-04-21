import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ExtractionSchema {
  schema: Record<string, any>;
  document_type: string;
  extraction_prompt?: string;
}

export interface ExtractionResult {
  task_id: string;
  status: string;
  extracted_data?: Record<string, any>;
  ocr_detections?: Array<{
    text: string;
    box: number[][];
    confidence: number;
    page_number: number;
  }>;
  error?: string;
}

export interface DocumentTemplate {
  name: string;
  schema: Record<string, any>;
}

export const documentAPI = {
  async processWithSchema(file: File, schema: ExtractionSchema): Promise<ExtractionResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('schema_data', JSON.stringify(schema));

    const response = await api.post<ExtractionResult>('/api/v1/document/process-with-schema', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async processBatch(files: File[], schema: ExtractionSchema) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    formData.append('schema_data', JSON.stringify(schema));

    const response = await api.post('/api/v1/document/extract-batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getTemplates(): Promise<Record<string, DocumentTemplate>> {
    const response = await api.get<Record<string, DocumentTemplate>>('/api/v1/document/templates');
    return response.data;
  },

  async getOCRStatus(taskId: string) {
    const response = await api.get(`/api/v1/ocr/results/${taskId}`);
    return response.data;
  },
};

export default api;
