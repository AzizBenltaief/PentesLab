import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, TrendingUp, Clock, Target, Star, MessageSquare } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../services/api';

const Statistics = () => {
  const [executionStats, setExecutionStats] = useState(null);
  const [coverageStats, setCoverageStats] = useState(null);
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const [execTime, coverage, feedback] = await Promise.all([
        api.get('/statistics/execution-times'),
        api.get('/coverage/stats/global'),
        api.get('/feedback/statistics')
      ]);

      setExecutionStats(execTime.data);
      setCoverageStats(coverage.data);
      setFeedbackStats(feedback.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  const timeDistributionData = executionStats?.time_distribution ? [
    { name: '0-30s', value: executionStats.time_distribution['0-30s'] },
    { name: '30-60s', value: executionStats.time_distribution['30-60s'] },
    { name: '60-120s', value: executionStats.time_distribution['60-120s'] },
    { name: '120s+', value: executionStats.time_distribution['120s+'] }
  ] : [];

  const categoryData = coverageStats?.category_averages ? Object.entries(coverageStats.category_averages).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    coverage: value
  })) : [];

  const feedbackCategoryData = feedbackStats?.category_ratings ? Object.entries(feedbackStats.category_ratings).map(([name, data]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    rating: data.avg_rating,
    responses: data.total_responses
  })) : [];

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Statistiques Avancées</h1>
        </div>

        {/* Execution Time Statistics */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-6">
            <Clock className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Temps d'Exécution</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Temps Moyen</p>
              <p className="text-2xl font-bold text-blue-600">{executionStats?.avg_time || 0}s</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Temps Min</p>
              <p className="text-2xl font-bold text-green-600">{executionStats?.min_time || 0}s</p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Temps Médian</p>
              <p className="text-2xl font-bold text-yellow-600">{executionStats?.median_time || 0}s</p>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Temps Max</p>
              <p className="text-2xl font-bold text-red-600">{executionStats?.max_time || 0}s</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Distribution des Temps</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={timeDistributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {timeDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Scans Récents</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {executionStats?.recent_scans?.slice(0, 5).map((scan) => (
                  <div key={scan.id} className="flex justify-between items-center bg-gray-50 p-3 rounded">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{scan.target}</p>
                      <p className="text-xs text-gray-500">{new Date(scan.created_at).toLocaleString()}</p>
                    </div>
                    <span className="text-sm font-semibold text-blue-600">{scan.execution_time}s</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Vulnerability Coverage Statistics */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-6">
            <Target className="h-6 w-6 text-green-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Couverture des Vulnérabilités</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Total Scans</p>
              <p className="text-2xl font-bold text-purple-600">{coverageStats?.total_scans || 0}</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Couverture Moyenne</p>
              <p className="text-2xl font-bold text-blue-600">{coverageStats?.avg_coverage || 0}%</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Meilleure Couverture</p>
              <p className="text-2xl font-bold text-green-600">{coverageStats?.best_coverage || 0}%</p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Pire Couverture</p>
              <p className="text-2xl font-bold text-yellow-600">{coverageStats?.worst_coverage || 0}%</p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Couverture par Catégorie</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Bar dataKey="coverage" fill="#3b82f6" name="Couverture (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* User Feedback Statistics */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-6">
            <Star className="h-6 w-6 text-yellow-500 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Évaluation Utilisateur</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-yellow-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Note Globale</p>
              <div className="flex items-center">
                <p className="text-3xl font-bold text-yellow-600">{feedbackStats?.overall_rating?.toFixed(1) || 0}</p>
                <span className="text-yellow-500 ml-2">★</span>
              </div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Total Évaluations</p>
              <p className="text-3xl font-bold text-blue-600">{feedbackStats?.total_feedback || 0}</p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Notes par Catégorie</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={feedbackCategoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 5]} />
                <Tooltip />
                <Legend />
                <Bar dataKey="rating" fill="#f59e0b" name="Note Moyenne" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {feedbackStats?.recent_comments && feedbackStats.recent_comments.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <MessageSquare className="h-5 w-5 mr-2" />
                Commentaires Récents
              </h3>
              <div className="space-y-3">
                {feedbackStats.recent_comments.slice(0, 5).map((comment, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <span className="inline-block bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
                        {comment.category}
                      </span>
                      <div className="flex items-center">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`h-4 w-4 ${i < comment.rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                          />
                        ))}
                      </div>
                    </div>
                    <p className="text-sm text-gray-700">{comment.comment}</p>
                    <p className="text-xs text-gray-500 mt-2">{new Date(comment.timestamp).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Statistics;
