import React from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { Activity, Plus } from 'lucide-react';

const Scans = () => {
  return (
    <Layout>
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="sm:flex sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Scans</h1>
            <p className="mt-2 text-sm text-gray-700">
              View and manage your penetration test scans
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <Link
              to="/scans/new"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Scan
            </Link>
          </div>
        </div>

        <div className="mt-8 text-center py-12">
          <Activity className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No scans</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new scan or view scans from your projects.
          </p>
          <div className="mt-6">
            <Link
              to="/scans/new"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Scan
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Scans;
