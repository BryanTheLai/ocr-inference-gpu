'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Plus, Trash2, Copy, Download, Upload, Save } from 'lucide-react';
import { cn } from '@/lib/utils';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface SchemaField {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description?: string;
  required?: boolean;
  properties?: SchemaField[];
  items?: SchemaField;
}

interface SchemaBuilderProps {
  initialSchema?: any;
  onSchemaChange: (schema: any) => void;
  templates?: Record<string, any>;
}

export default function SchemaBuilder({ 
  initialSchema = {}, 
  onSchemaChange,
  templates = {}
}: SchemaBuilderProps) {
  const [mode, setMode] = useState<'visual' | 'json'>('visual');
  const [jsonSchema, setJsonSchema] = useState(JSON.stringify(initialSchema, null, 2));
  const [fields, setFields] = useState<SchemaField[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  useEffect(() => {
    try {
      const parsed = JSON.parse(jsonSchema);
      onSchemaChange(parsed);
      if (mode === 'json') {
        convertJsonToFields(parsed);
      }
    } catch (e) {
      console.error('Invalid JSON schema');
    }
  }, [jsonSchema, mode]);

  const convertJsonToFields = (schema: any) => {
    if (schema.properties) {
      const newFields: SchemaField[] = Object.entries(schema.properties).map(([name, prop]: [string, any]) => ({
        name,
        type: prop.type || 'string',
        description: prop.description,
        required: schema.required?.includes(name),
        properties: prop.properties ? convertPropertiesToFields(prop.properties) : undefined,
        items: prop.items
      }));
      setFields(newFields);
    }
  };

  const convertPropertiesToFields = (properties: any): SchemaField[] => {
    return Object.entries(properties).map(([name, prop]: [string, any]) => ({
      name,
      type: prop.type || 'string',
      description: prop.description,
      properties: prop.properties ? convertPropertiesToFields(prop.properties) : undefined,
      items: prop.items
    }));
  };

  const convertFieldsToJson = () => {
    const schema: any = {
      type: 'object',
      properties: {},
      required: []
    };

    fields.forEach(field => {
      schema.properties[field.name] = {
        type: field.type,
        description: field.description
      };

      if (field.type === 'object' && field.properties) {
        schema.properties[field.name].properties = {};
        field.properties.forEach(subField => {
          schema.properties[field.name].properties[subField.name] = {
            type: subField.type,
            description: subField.description
          };
        });
      }

      if (field.type === 'array' && field.items) {
        schema.properties[field.name].items = field.items;
      }

      if (field.required) {
        schema.required.push(field.name);
      }
    });

    return schema;
  };

  const addField = () => {
    setFields([...fields, {
      name: `field_${fields.length + 1}`,
      type: 'string',
      description: '',
      required: false
    }]);
  };

  const updateField = (index: number, updates: Partial<SchemaField>) => {
    const newFields = [...fields];
    newFields[index] = { ...newFields[index], ...updates };
    setFields(newFields);
    
    if (mode === 'visual') {
      const schema = convertFieldsToJson();
      setJsonSchema(JSON.stringify(schema, null, 2));
    }
  };

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
    if (mode === 'visual') {
      const newFields = fields.filter((_, i) => i !== index);
      const schema = convertFieldsToJson();
      setJsonSchema(JSON.stringify(schema, null, 2));
    }
  };

  const addSubField = (parentIndex: number) => {
    const newFields = [...fields];
    if (!newFields[parentIndex].properties) {
      newFields[parentIndex].properties = [];
    }
    newFields[parentIndex].properties!.push({
      name: `subfield_${newFields[parentIndex].properties!.length + 1}`,
      type: 'string',
      description: ''
    });
    setFields(newFields);
  };

  const loadTemplate = (templateKey: string) => {
    if (templates[templateKey]) {
      const template = templates[templateKey];
      setJsonSchema(JSON.stringify(template.schema, null, 2));
      convertJsonToFields(template.schema);
      setSelectedTemplate(templateKey);
    }
  };

  const exportSchema = () => {
    const blob = new Blob([jsonSchema], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'schema.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const importSchema = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setJsonSchema(content);
        try {
          const parsed = JSON.parse(content);
          convertJsonToFields(parsed);
        } catch (err) {
          console.error('Invalid JSON file');
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setMode('visual')}
            className={cn(
              "px-4 py-2 rounded-lg font-medium transition-colors",
              mode === 'visual' 
                ? "bg-blue-500 text-white" 
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            )}
          >
            Visual Builder
          </button>
          <button
            onClick={() => setMode('json')}
            className={cn(
              "px-4 py-2 rounded-lg font-medium transition-colors",
              mode === 'json' 
                ? "bg-blue-500 text-white" 
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            )}
          >
            JSON Editor
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={selectedTemplate}
            onChange={(e) => loadTemplate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="">Select Template</option>
            {Object.entries(templates).map(([key, template]: [string, any]) => (
              <option key={key} value={key}>{template.name}</option>
            ))}
          </select>

          <label className="cursor-pointer">
            <input
              type="file"
              accept=".json"
              onChange={importSchema}
              className="hidden"
            />
            <div className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Upload className="w-5 h-5 text-gray-600" />
            </div>
          </label>

          <button
            onClick={exportSchema}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Download className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      {mode === 'visual' ? (
        <div className="flex-1 overflow-auto">
          <div className="space-y-4">
            {fields.map((field, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="grid grid-cols-4 gap-4 mb-2">
                  <input
                    type="text"
                    value={field.name}
                    onChange={(e) => updateField(index, { name: e.target.value })}
                    placeholder="Field name"
                    className="px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <select
                    value={field.type}
                    onChange={(e) => updateField(index, { type: e.target.value as any })}
                    className="px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="string">String</option>
                    <option value="number">Number</option>
                    <option value="boolean">Boolean</option>
                    <option value="object">Object</option>
                    <option value="array">Array</option>
                  </select>
                  <input
                    type="text"
                    value={field.description || ''}
                    onChange={(e) => updateField(index, { description: e.target.value })}
                    placeholder="Description"
                    className="px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <div className="flex items-center space-x-2">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={field.required || false}
                        onChange={(e) => updateField(index, { required: e.target.checked })}
                        className="rounded"
                      />
                      <span className="text-sm">Required</span>
                    </label>
                    {field.type === 'object' && (
                      <button
                        onClick={() => addSubField(index)}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => removeField(index)}
                      className="p-1 hover:bg-red-100 rounded text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {field.type === 'object' && field.properties && (
                  <div className="ml-8 mt-4 space-y-2">
                    {field.properties.map((subField, subIndex) => (
                      <div key={subIndex} className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={subField.name}
                          onChange={(e) => {
                            const newFields = [...fields];
                            newFields[index].properties![subIndex].name = e.target.value;
                            setFields(newFields);
                          }}
                          placeholder="Property name"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                        />
                        <select
                          value={subField.type}
                          onChange={(e) => {
                            const newFields = [...fields];
                            newFields[index].properties![subIndex].type = e.target.value as any;
                            setFields(newFields);
                          }}
                          className="px-3 py-2 border border-gray-300 rounded-lg"
                        >
                          <option value="string">String</option>
                          <option value="number">Number</option>
                          <option value="boolean">Boolean</option>
                        </select>
                        <input
                          type="text"
                          value={subField.description || ''}
                          onChange={(e) => {
                            const newFields = [...fields];
                            newFields[index].properties![subIndex].description = e.target.value;
                            setFields(newFields);
                          }}
                          placeholder="Description"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            <button
              onClick={addField}
              className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 transition-colors flex items-center justify-center space-x-2"
            >
              <Plus className="w-5 h-5" />
              <span>Add Field</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1">
          <MonacoEditor
            height="100%"
            language="json"
            theme="vs-light"
            value={jsonSchema}
            onChange={(value) => setJsonSchema(value || '')}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              wordWrap: 'on',
              automaticLayout: true,
              formatOnPaste: true,
              formatOnType: true,
            }}
          />
        </div>
      )}
    </div>
  );
}
