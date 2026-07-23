import { FormEvent, useEffect, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { TemplateCard } from "../components/TemplateCard";
import { TemplateForm } from "../components/TemplateForm";
import { Template, TemplateFormData, emptyTemplateForm } from "../types/templates";
import "./TemplatesPage.css";

import { API_BASE, getAuthHeaders } from "../lib/api";

const resolvedApiBase = API_BASE;

export function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [templateError, setTemplateError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [formData, setFormData] = useState<TemplateFormData>(emptyTemplateForm);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${resolvedApiBase}/templates`, {
        headers: getAuthHeaders(),
      });
      await assertOk(response);
      setTemplates(await response.json());
      setTemplateError(null);
    } catch (err) {
      setTemplates([]);
      setTemplateError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    try {
      const response = await fetch(templateUrl(editingTemplate), {
        method: editingTemplate ? "PUT" : "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(formData),
      });
      await assertOk(response);
      await loadTemplates();
      closeForm();
    } catch (err) {
      setTemplateError((err as Error).message);
    }
  };

  const handleEdit = (template: Template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      role: template.role,
      location: template.location,
      duration_hours: template.duration_hours,
      pay_rate: template.pay_rate,
      workers_needed: template.workers_needed,
      notes: template.notes || "",
    });
    setShowCreateForm(true);
  };

  const handleDelete = async (templateId: string) => {
    if (!confirm("Are you sure you want to delete this template?")) return;

    try {
      const response = await fetch(`${resolvedApiBase}/templates/${templateId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      await assertOk(response);
      await loadTemplates();
    } catch (err) {
      setTemplateError((err as Error).message);
    }
  };

  const openCreateForm = () => {
    setEditingTemplate(null);
    setFormData(emptyTemplateForm);
    setShowCreateForm(true);
  };

  const closeForm = () => {
    setShowCreateForm(false);
    setEditingTemplate(null);
    setFormData(emptyTemplateForm);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Shift Templates</h1>
          <p className="page-subtitle">Create and manage reusable shift templates</p>
        </div>
        <button className="btn primary" onClick={openCreateForm}>
          Create Template
        </button>
      </div>

      {templateError && (
        <div className="card error-card">
          <p className="status error" style={{ margin: 0 }}>{templateError}</p>
        </div>
      )}

      {showCreateForm && (
        <TemplateForm
          editingTemplate={editingTemplate}
          formData={formData}
          onChange={setFormData}
          onSubmit={handleSubmit}
          onCancel={closeForm}
        />
      )}

      {renderTemplates({
        loading,
        templates,
        openCreateForm,
        handleEdit,
        handleDelete,
      })}
    </div>
  );
}

function renderTemplates({
  loading,
  templates,
  openCreateForm,
  handleEdit,
  handleDelete,
}: {
  loading: boolean;
  templates: Template[];
  openCreateForm: () => void;
  handleEdit: (template: Template) => void;
  handleDelete: (templateId: string) => void;
}) {
  if (loading) {
    return (
      <div className="card templates-loading">
        <p>Loading templates...</p>
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <EmptyState
        title="No templates yet"
        message="Create your first shift template to save time when posting similar shifts."
        action={{
          label: "Create Template",
          onClick: openCreateForm,
        }}
      />
    );
  }

  return (
    <div className="templates-grid">
      {templates.map((template) => (
        <TemplateCard
          key={template.template_id}
          template={template}
          onEdit={() => handleEdit(template)}
          onDelete={() => handleDelete(template.template_id)}
        />
      ))}
    </div>
  );
}

function templateUrl(editingTemplate: Template | null) {
  if (editingTemplate) {
    return `${resolvedApiBase}/templates/${editingTemplate.template_id}`;
  }
  return `${resolvedApiBase}/templates`;
}

async function assertOk(response: Response) {
  if (response.ok) return;
  const errorPayload = await response.json();
  throw new Error(errorPayload?.detail ?? `API error: ${response.status}`);
}
