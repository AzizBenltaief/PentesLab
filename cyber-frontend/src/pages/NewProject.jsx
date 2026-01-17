import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { projectAPI } from '../services/api';
import { Save, X, Plus, Trash2 } from 'lucide-react';

const NewProject = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targets, setTargets] = useState(['']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleAddTarget = () => {
    setTargets([...targets, '']);
  };

  const handleRemoveTarget = (index) => {
    setTargets(targets.filter((_, i) => i !== index));
  };

  const handleTargetChange = (index, value) => {
    const newTargets = [...targets];
    newTargets[index] = value;
    setTargets(newTargets);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const validTargets = targets.filter(t => t.trim() !== '');
    
    if (validTargets.length === 0) {
      setError('Please add at least one target');
      return;
    }

    setLoading(true);

    try {
      await projectAPI.create({
        name,
        description,
        scope: validTargets
      });
      navigate('/projects');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="md:flex md:items-center md:justify-between">
            <h1 className="text-2xl font-bold text-gray-900">New Project</h1>
          </div>

          <form onSubmit={handleSubmit} className="mt-8 space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div className="bg-white shadow rounded-lg p-6">
              <div className="space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="My Pentest Project"
                  />
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    id="description"
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Describe the purpose of this project..."
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Authorized Targets (Scope) *
                    </label>
                    <button
                      type="button"
                      onClick={handleAddTarget}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200"
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Add Target
                    </button>
                  </div>
                  <p className="text-sm text-gray-500 mb-3">
                    Define IP addresses, domains, or URLs authorized for scanning
                  </p>
                  <div className="space-y-3">
                    {targets.map((target, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={target}
                          onChange={(e) => handleTargetChange(index, e.target.value)}
                          className="flex-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="e.g., 192.168.1.1, example.com, https://target.com"
                        />
                        {targets.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveTarget(index)}
                            className="inline-flex items-center px-3 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate('/projects')}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
              >
                <Save className="h-4 w-4 mr-2" />
                {loading ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
};

export default NewProject;
