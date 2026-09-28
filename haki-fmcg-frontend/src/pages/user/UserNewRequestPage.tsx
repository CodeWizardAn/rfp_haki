import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Upload,
  Plus,
  Trash2,
  ArrowLeft,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Button, Input, TextArea } from '@/components/ui';

interface LineItem {
  id: number;
  description: string;
  quantity: number;
  unit: string;
  specifications: string;
  estimatedBudget: string;
}

export default function UserNewRequestPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [deadline, setDeadline] = useState('');
  const [priority, setPriority] = useState('medium');
  const [category, setCategory] = useState('');
  const [lineItems, setLineItems] = useState<LineItem[]>([
    { id: 1, description: '', quantity: 1, unit: 'units', specifications: '', estimatedBudget: '' },
  ]);
  const [attachments, setAttachments] = useState<File[]>([]);

  const addLineItem = () => {
    setLineItems([
      ...lineItems,
      { id: Date.now(), description: '', quantity: 1, unit: 'units', specifications: '', estimatedBudget: '' },
    ]);
  };

  const removeLineItem = (id: number) => {
    if (lineItems.length > 1) {
      setLineItems(lineItems.filter((item) => item.id !== id));
    }
  };

  const updateLineItem = (id: number, field: keyof LineItem, value: string | number) => {
    setLineItems(lineItems.map((item) => item.id === id ? { ...item, [field]: value } : item));
  };

  const handleSubmit = (_asDraft?: boolean) => {
    // Would call API here
    navigate('/user/requests');
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 max-w-4xl">
      <button
        onClick={() => navigate('/user/requests')}
        className="inline-flex items-center gap-2 text-sm text-muted-silver hover:text-ghost-white transition-colors"
      >
        <ArrowLeft size={16} />
        Back to Requests
      </button>

      <div>
        <h1 className="text-2xl font-bold text-ghost-white">New Procurement Request</h1>
        <p className="text-body text-muted-silver mt-1">Fill in the details to submit a new procurement request</p>
      </div>

      {/* Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle>Request Details</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          <Input
            label="Request Title"
            placeholder="e.g., Electrical Cables for Nairobi Office"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          <TextArea
            label="Description"
            placeholder="Describe the procurement requirement, including any special conditions..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-caption text-muted-silver mb-1.5">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full glass-input px-3 py-2.5 text-body text-ghost-white rounded-[10px]"
              >
                <option value="" className="bg-deep-navy">Select category</option>
                <option value="cables" className="bg-deep-navy">Cables & Wires</option>
                <option value="fmcg" className="bg-deep-navy">FMCG Products</option>
                <option value="safety" className="bg-deep-navy">Safety Equipment</option>
                <option value="electrical" className="bg-deep-navy">Electrical</option>
                <option value="industrial" className="bg-deep-navy">Industrial</option>
                <option value="office" className="bg-deep-navy">Office Supplies</option>
              </select>
            </div>

            <div>
              <label className="block text-caption text-muted-silver mb-1.5">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full glass-input px-3 py-2.5 text-body text-ghost-white rounded-[10px]"
              >
                <option value="low" className="bg-deep-navy">Low</option>
                <option value="medium" className="bg-deep-navy">Medium</option>
                <option value="high" className="bg-deep-navy">High</option>
                <option value="critical" className="bg-deep-navy">Critical</option>
              </select>
            </div>

            <Input
              label="Submission Deadline"
              type="date"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
            />
          </div>
        </div>
      </Card>

      {/* Line Items */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>Line Items</CardTitle>
          <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />} onClick={addLineItem}>
            Add Item
          </Button>
        </CardHeader>

        <div className="space-y-4">
          {lineItems.map((item, idx) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-xl bg-steel-slate/10 border border-steel-slate/20"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-muted-silver font-semibold">Item #{idx + 1}</span>
                {lineItems.length > 1 && (
                  <button
                    onClick={() => removeLineItem(item.id)}
                    className="p-1 rounded text-muted-silver hover:text-coral-flame transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input
                  placeholder="Item description"
                  value={item.description}
                  onChange={(e) => updateLineItem(item.id, 'description', e.target.value)}
                />
                <Input
                  placeholder="Specifications"
                  value={item.specifications}
                  onChange={(e) => updateLineItem(item.id, 'specifications', e.target.value)}
                />
                <div className="grid grid-cols-3 gap-2">
                  <Input
                    placeholder="Qty"
                    type="number"
                    value={String(item.quantity)}
                    onChange={(e) => updateLineItem(item.id, 'quantity', parseInt(e.target.value) || 1)}
                  />
                  <select
                    value={item.unit}
                    onChange={(e) => updateLineItem(item.id, 'unit', e.target.value)}
                    className="glass-input px-3 py-2.5 text-body text-ghost-white rounded-[10px]"
                  >
                    <option value="units" className="bg-deep-navy">Units</option>
                    <option value="meters" className="bg-deep-navy">Meters</option>
                    <option value="kg" className="bg-deep-navy">Kg</option>
                    <option value="liters" className="bg-deep-navy">Liters</option>
                    <option value="boxes" className="bg-deep-navy">Boxes</option>
                    <option value="sets" className="bg-deep-navy">Sets</option>
                  </select>
                  <Input
                    placeholder="Est. Budget"
                    value={item.estimatedBudget}
                    onChange={(e) => updateLineItem(item.id, 'estimatedBudget', e.target.value)}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </Card>

      {/* Attachments */}
      <Card>
        <CardHeader>
          <CardTitle>Attachments</CardTitle>
        </CardHeader>
        <div
          className="border-2 border-dashed border-steel-slate/30 rounded-xl p-8 text-center hover:border-electric-cyan/30 transition-colors cursor-pointer"
          onClick={() => document.getElementById('file-upload')?.click()}
        >
          <Upload size={32} className="text-muted-silver/40 mx-auto mb-3" />
          <p className="text-sm text-muted-silver">Drag & drop files here, or click to browse</p>
          <p className="text-xs text-muted-silver/60 mt-1">PDF, Excel, Word — Max 50MB each</p>
          <input
            id="file-upload"
            type="file"
            multiple
            className="hidden"
            onChange={(e) => setAttachments([...attachments, ...Array.from(e.target.files || [])])}
          />
        </div>
        {attachments.length > 0 && (
          <div className="mt-3 space-y-2">
            {attachments.map((file, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-steel-slate/10">
                <span className="text-sm text-ghost-white">{file.name}</span>
                <button
                  onClick={() => setAttachments(attachments.filter((_, i) => i !== idx))}
                  className="text-muted-silver hover:text-coral-flame"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-steel-slate/20">
        <Button variant="ghost" onClick={() => navigate('/user/requests')}>
          Cancel
        </Button>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => handleSubmit(true)}>
            Save as Draft
          </Button>
          <Button variant="primary" leftIcon={<FileText size={16} />} onClick={() => handleSubmit(false)}>
            Submit Request
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
