import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { metricsAPI } from '../services/api';
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  FolderOpen, 
  Clock,
  TrendingUp,
  Plus,
  PlayCircle,
  ArrowRight
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const response = await metricsAPI.getDashboard();
      setMetrics(response.data);
    } catch (err) {
      console.error('Failed to load metrics', err);
    } finally {
      setLoading(false);
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

  const scanStatusData = [
    { name: 'Completed', value: metrics?.completed_scans || 0, color: '#10b981' },
    { name: 'Running', value: metrics?.running_scans || 0, color: '#f59e0b' },
    { name: 'Failed', value: metrics?.failed_scans || 0, color: '#ef4444' },
  ];

  const stats = [
    {
      name: 'Total Scans',
      value: metrics?.total_scans || 0,
      icon: Activity,
      bgColor: 'from-blue-500 to-blue-600',
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600'
    },
    {
      name: 'Completed',
      value: metrics?.completed_scans || 0,
      icon: CheckCircle,
      bgColor: 'from-green-500 to-green-600',
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600'
    },
    {
      name: 'Vulnerabilities',
      value: metrics?.total_vulnerabilities || 0,
      icon: AlertTriangle,
      bgColor: 'from-red-500 to-red-600',
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600'
    },
    {
      name: 'Active Projects',
      value: metrics?.active_projects || 0,
      icon: FolderOpen,
      bgColor: 'from-purple-500 to-purple-600',
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600'
    }
  ];

  return (
    <Layout>
      <div className="px-4 sm:px-6 lg:px-8 py-8 bg-gray-50 min-h-screen">
        {/* Header with Quick Actions */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="mt-2 text-gray-600">
                Monitor your penetration testing activities and results
              </p>
            </div>
            <div className="flex gap-3">
              <Link
                to="/projects/new"
                className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg shadow-sm transition gap-2"
              >
                <Plus className="h-5 w-5" />
                New Project
              </Link>
              <Link
                to="/scans/new"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-lg shadow-sm transition gap-2"
              >
                <PlayCircle className="h-5 w-5" />
                Start Scan
              </Link>
            </div>
          </div>
        </div>

        {/* Welcome Guide - Show when no scans */}
        {metrics?.total_scans === 0 && (
          <div className="mb-8 bg-gradient-to-r from-purple-50 to-blue-50 border-l-4 border-purple-500 p-6 rounded-lg shadow-sm">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <Activity className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4 flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Welcome to PENTESTLAB! 👋
                </h3>
                <p className="text-gray-700 mb-4">
                  Get started by creating your first project and running a security scan. Here's how:
                </p>
                <ol className="list-decimal list-inside space-y-2 text-gray-700 mb-4">
                  <li>Create a new project with target scope (IPs, domains)</li>
                  <li>Start a scan with your preferred scanning options</li>
                  <li>Monitor real-time progress and review results</li>
                  <li>Export reports and remediation recommendations</li>
                </ol>
                <div className="flex gap-3">
                  <Link
                    to="/projects/new"
                    className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition gap-2"
                  >
                    Create First Project
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.name} className="bg-white overflow-hidden shadow-lg rounded-xl border border-gray-100 hover:shadow-xl transition-shadow">
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        {stat.name}
                      </p>
                      <p className="text-3xl font-bold text-gray-900">
                        {stat.value}
                      </p>
                    </div>
                    <div className={`${stat.iconBg} p-4 rounded-xl`}>
                      <Icon className={`h-8 w-8 ${stat.iconColor}`} />
                    </div>
                  </div>
                </div>
                <div className={`h-2 bg-gradient-to-r ${stat.bgColor}`}></div>
              </div>
            );
          })}
        </div>

        {/* Charts */}
        <div className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-2">
          {/* Scan Status Distribution */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Scan Status Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={scanStatusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {scanStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Project Overview */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Project Overview</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-purple-600">Total Projects</p>
                  <p className="text-3xl font-bold text-purple-900">{metrics?.total_projects || 0}</p>
                </div>
                <FolderOpen className="h-12 w-12 text-purple-400" />
              </div>
              <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-green-600">Active Projects</p>
                  <p className="text-3xl font-bold text-green-900">{metrics?.active_projects || 0}</p>
                </div>
                <Activity className="h-12 w-12 text-green-400" />
              </div>
              <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-red-600">Total Vulnerabilities Found</p>
                  <p className="text-3xl font-bold text-red-900">{metrics?.total_vulnerabilities || 0}</p>
                </div>
                <AlertTriangle className="h-12 w-12 text-red-400" />
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <a
              href="/projects/new"
              className="flex items-center justify-center px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <FolderOpen className="h-5 w-5 mr-2" />
              New Project
            </a>
            <a
              href="/scans/new"
              className="flex items-center justify-center px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
            >
              <Activity className="h-5 w-5 mr-2" />
              Start Scan
            </a>
            <a
              href="/audit"
              className="flex items-center justify-center px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              View Audit Logs
            </a>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
