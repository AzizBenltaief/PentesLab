import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { scanAPI } from '../services/api';
import { ArrowLeft, Activity, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

const ScanDetail = () => {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadScan();
    
    // Poll for updates if scan is running
    const interval = setInterval(() => {
      if (scan?.status === 'running') {
        loadScan();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [id, scan?.status]);

  const loadScan = async () => {
    try {
      const response = await scanAPI.getStatus(id);
      setScan(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to load scan details');
      setLoading(false);
    }
  };

  const getStepName = (step) => {
    const steps = [
      'Passive Reconnaissance',
      'Footprinting',
      'Network Scanning',
      'Web Vulnerability Scanning',
      'OpenVAS Assessment',
      'Exploitation Analysis',
      'Post-Exploitation',
      'Persistence Analysis',
      'Report Generation'
    ];
    return steps[step] || `Step ${step}`;
  };

  const StatusIcon = ({ status }) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case 'running':
        return <Clock className="h-6 w-6 text-yellow-500 animate-spin" />;
      case 'failed':
        return <XCircle className="h-6 w-6 text-red-500" />;
      default:
        return <Activity className="h-6 w-6 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (!scan) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-500">Scan not found</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link to="/scans" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Scans
          </Link>
        </div>

        <div className="bg-white shadow rounded-lg">
          {/* Header */}
          <div className="px-6 py-5 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Scan Details</h1>
                <p className="mt-1 text-sm text-gray-500">ID: {scan.id}</p>
              </div>
              <div className="flex items-center space-x-3">
                <StatusIcon status={scan.status} />
                <span
                  className={`px-3 py-1 text-sm font-medium rounded-full ${
                    scan.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : scan.status === 'running'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {scan.status}
                </span>
              </div>
            </div>
          </div>

          {error && (
            <div className="px-6 py-4 bg-red-50 border-b border-red-200">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Progress */}
          <div className="px-6 py-5 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Progress</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-gray-700">
                  {getStepName(scan.step)}
                </span>
                <span className="text-gray-500">
                  Step {scan.step + 1} of 9
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${((scan.step + 1) / 9) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Stats */}
          {scan.status === 'completed' && (
            <div className="px-6 py-5 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Summary</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-red-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-red-600">Vulnerabilities</p>
                  <p className="mt-2 text-3xl font-bold text-red-900">{scan.vulns || 0}</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-blue-600">Execution Time</p>
                  <p className="mt-2 text-3xl font-bold text-blue-900">
                    {scan.execution_time ? `${scan.execution_time}s` : 'N/A'}
                  </p>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-green-600">Success Rate</p>
                  <p className="mt-2 text-3xl font-bold text-green-900">
                    {scan.success_rate || 0}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Logs */}
          <div className="px-6 py-5">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Execution Logs</h3>
            <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
              {scan.logs && scan.logs.length > 0 ? (
                <div className="space-y-1">
                  {scan.logs.map((log, index) => (
                    <div key={index} className="text-sm font-mono text-green-400">
                      <span className="text-gray-500">[{index + 1}]</span> {log}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No logs available</p>
              )}
            </div>
          </div>

          {/* Results */}
          {scan.status === 'completed' && scan.results && (
            <div className="px-6 py-5 border-t border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Scan Results</h3>
              <Link
                to={`/scans/${id}/results`}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                View Detailed Results
              </Link>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default ScanDetail;
