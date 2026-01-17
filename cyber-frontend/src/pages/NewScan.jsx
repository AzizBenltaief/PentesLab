import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Layout from '../components/Layout';
import { scanAPI, projectAPI } from '../services/api';
import { Play, AlertCircle, Target } from 'lucide-react';

const NewScan = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [targetUrl, setTargetUrl] = useState('');
  const [projectId, setProjectId] = useState(location.state?.projectId || '');
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await projectAPI.list();
      setProjects(response.data.projects.filter(p => p.status === 'active'));
    } catch (err) {
      console.error('Failed to load projects', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await scanAPI.start({
        target_url: targetUrl,
        project_id: projectId || null
      });
      
      navigate(`/scans/${response.data.scan_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start scan');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <Target className="mx-auto h-12 w-12 text-blue-600" />
            <h1 className="mt-3 text-3xl font-bold text-gray-900">Start New Scan</h1>
            <p className="mt-2 text-sm text-gray-600">
              Configure and launch a penetration test
            </p>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <div className="flex">
                    <AlertCircle className="h-5 w-5 text-red-400" />
                    <div className="ml-3">
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <label htmlFor="project" className="block text-sm font-medium text-gray-700">
                  Project (Optional)
                </label>
                <select
                  id="project"
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">No Project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
                <p className="mt-2 text-sm text-gray-500">
                  Select a project to validate the target against authorized scope
                </p>
              </div>

              <div>
                <label htmlFor="target" className="block text-sm font-medium text-gray-700">
                  Target URL *
                </label>
                <input
                  type="text"
                  id="target"
                  required
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="https://example.com or 192.168.1.1"
                />
                <p className="mt-2 text-sm text-gray-500">
                  Enter the IP address, domain, or URL to scan
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Scan Workflow</h4>
                <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                  <li>Passive Reconnaissance (WHOIS, DNS, Certificate Transparency)</li>
                  <li>Footprinting (HTTP Header Analysis)</li>
                  <li>Network Scanning (Nmap Port Discovery)</li>
                  <li>Web Vulnerability Scanning (Nikto, Gobuster)</li>
                  <li>OpenVAS Vulnerability Assessment</li>
                  <li>Exploitation Analysis</li>
                  <li>Post-Exploitation Analysis</li>
                  <li>Persistence Analysis</li>
                  <li>AI-Powered Report Generation</li>
                </ol>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => navigate(-1)}
                  className="px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  <Play className="h-4 w-4 mr-2" />
                  {loading ? 'Starting Scan...' : 'Start Scan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default NewScan;
