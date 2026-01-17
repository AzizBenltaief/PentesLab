import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { scanAPI } from '../services/api';
import { 
  ArrowLeft, 
  AlertTriangle, 
  Shield, 
  Server, 
  Globe, 
  FileText,
  Search,
  Lock,
  Eye
} from 'lucide-react';

const ScanResults = () => {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    loadScanResults();
  }, [id]);

  const loadScanResults = async () => {
    try {
      const response = await scanAPI.getStatus(id);
      console.log('=== SCAN DATA DEBUG ===');
      console.log('Full scan object:', response.data);
      console.log('Scan status:', response.data?.status);
      console.log('Results object:', response.data?.results);
      console.log('Results keys:', response.data?.results ? Object.keys(response.data.results) : 'NO RESULTS');
      console.log('Nikto data:', response.data?.results?.nikto);
      console.log('Gobuster data:', response.data?.results?.gobuster);
      console.log('OpenVAS data:', response.data?.results?.openvas);
      console.log('Certificates:', response.data?.results?.certificates);
      console.log('Threat Intel:', response.data?.results?.threat_intel);
      console.log('=======================');
      setScan(response.data);
    } catch (err) {
      console.error('Failed to load scan results', err);
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

  if (!scan || !scan.results) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-500">No results available</p>
        </div>
      </Layout>
    );
  }

  const tabs = [
    { id: 'summary', label: 'Summary', icon: Eye },
    { id: 'reconnaissance', label: 'Reconnaissance', icon: Search },
    { id: 'vulnerabilities', label: 'Vulnerabilities', icon: AlertTriangle },
    { id: 'network', label: 'Network', icon: Server },
    { id: 'web', label: 'Web Scanning', icon: Globe },
    { id: 'report', label: 'AI Report', icon: FileText },
  ];

  return (
    <Layout>
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link to={`/scans/${id}`} className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Scan Details
          </Link>
        </div>

        <div className="bg-white shadow rounded-lg">
          {/* Header */}
          <div className="px-6 py-5 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-gray-900">Scan Results</h1>
            <p className="mt-1 text-sm text-gray-500">Detailed analysis and findings</p>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px overflow-x-auto">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm flex items-center ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="px-6 py-6">
            {activeTab === 'summary' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-red-50 rounded-lg p-4">
                    <AlertTriangle className="h-8 w-8 text-red-600 mb-2" />
                    <p className="text-sm font-medium text-red-600">Vulnerabilities</p>
                    <p className="text-3xl font-bold text-red-900">{scan.vulns || 0}</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <Server className="h-8 w-8 text-blue-600 mb-2" />
                    <p className="text-sm font-medium text-blue-600">Open Ports</p>
                    <p className="text-3xl font-bold text-blue-900">
                      {scan.results.open_ports?.length || 0}
                    </p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <Shield className="h-8 w-8 text-green-600 mb-2" />
                    <p className="text-sm font-medium text-green-600">Completion</p>
                    <p className="text-3xl font-bold text-green-900">{scan.success_rate}%</p>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Key Findings</h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    <p className="text-sm text-gray-700">
                      • Completed all 9 phases of penetration testing workflow
                    </p>
                    <p className="text-sm text-gray-700">
                      • Execution time: {scan.execution_time}s
                    </p>
                    <p className="text-sm text-gray-700">
                      • Scanned target with comprehensive vulnerability assessment
                    </p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'reconnaissance' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">WHOIS Information</h3>
                  {scan.results.whois && Object.keys(scan.results.whois).length > 0 ? (
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      <div className="space-y-1">
                        <div><span className="text-green-600">Domain:</span> {scan.results.whois.domain_name}</div>
                        <div><span className="text-green-600">Organization:</span> {scan.results.whois.organization}</div>
                        <div><span className="text-green-600">Registrar:</span> {scan.results.whois.registrar}</div>
                        <div><span className="text-green-600">Created:</span> {scan.results.whois.creation_date}</div>
                        <div><span className="text-green-600">Expires:</span> {scan.results.whois.expiration_date}</div>
                        <div><span className="text-green-600">Status:</span> {scan.results.whois.status}</div>
                        <div><span className="text-green-600">Name Servers:</span> {scan.results.whois.name_servers?.join(', ')}</div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No WHOIS data available</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">DNS Records</h3>
                  {scan.results.dns && Object.keys(scan.results.dns).length > 0 ? (
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      <div className="space-y-1">
                        {scan.results.dns.A && <div><span className="text-green-600">A Record:</span> {scan.results.dns.A}</div>}
                        {scan.results.dns.MX && <div><span className="text-green-600">MX Records:</span> {scan.results.dns.MX.join(', ')}</div>}
                        {scan.results.dns.NS && <div><span className="text-green-600">NS Records:</span> {scan.results.dns.NS.join(', ')}</div>}
                        {scan.results.dns.TXT && <div><span className="text-green-600">TXT Records:</span> {scan.results.dns.TXT.join(', ')}</div>}
                        {scan.results.dns.subdomains && scan.results.dns.subdomains.length > 0 && (
                          <div><span className="text-green-600">Subdomains:</span> {scan.results.dns.subdomains.join(', ')}</div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No DNS data available</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Certificate Transparency</h3>
                  {scan.results.certificates && Object.keys(scan.results.certificates).length > 0 ? (
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      <div className="space-y-1">
                        <div><span className="text-green-600">Certificates Found:</span> {scan.results.certificates.cert_count}</div>
                        {scan.results.certificates.discovered_domains && scan.results.certificates.discovered_domains.length > 0 && (
                          <div><span className="text-green-600">Discovered Domains:</span> {scan.results.certificates.discovered_domains.join(', ')}</div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No certificate transparency data available</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Threat Intelligence</h3>
                  {scan.results.threat_intel && Object.keys(scan.results.threat_intel).length > 0 ? (
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      <div className="space-y-1">
                        <div><span className="text-green-600">IP Address:</span> {scan.results.threat_intel.ip}</div>
                        <div><span className="text-green-600">ISP:</span> {scan.results.threat_intel.isp}</div>
                        <div><span className="text-green-600">Location:</span> {scan.results.threat_intel.location}</div>
                        {scan.results.threat_intel.open_ports && (
                          <div><span className="text-green-600">Known Open Ports:</span> {scan.results.threat_intel.open_ports.join(', ')}</div>
                        )}
                        {scan.results.threat_intel.vulnerabilities && (
                          <div><span className="text-green-600">Known Vulnerabilities:</span> {scan.results.threat_intel.vulnerabilities}</div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No threat intelligence data available</p>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'vulnerabilities' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">OpenVAS Findings</h3>
                  {scan.results.vulnerabilities_enriched?.length > 0 ? (
                    <div className="space-y-3">
                      {scan.results.vulnerabilities_enriched.map((vuln, index) => (
                        <div
                          key={index}
                          className="border border-red-200 bg-red-50 rounded-lg p-4"
                        >
                          <div className="flex items-start">
                            <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                            <div className="ml-3 flex-1">
                              <h4 className="text-sm font-medium text-red-900">
                                {vuln.nvt || vuln.name || 'Vulnerability Found'}
                              </h4>
                              <p className="mt-1 text-sm text-red-700">
                                {vuln.description || 'No description available'}
                              </p>
                              <div className="mt-2 flex items-center gap-4">
                                {vuln.cvss && (
                                  <span className={`text-xs px-2 py-1 rounded ${
                                    vuln.cvss >= 7 ? 'bg-red-100 text-red-800' :
                                    vuln.cvss >= 4 ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-blue-100 text-blue-800'
                                  }`}>
                                    CVSS: {vuln.cvss}
                                  </span>
                                )}
                                {vuln.severity && (
                                  <span className={`text-xs px-2 py-1 rounded ${
                                    vuln.severity === 'Critical' || vuln.severity === 'High' ? 'bg-red-100 text-red-800' :
                                    vuln.severity === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-blue-100 text-blue-800'
                                  }`}>
                                    {vuln.severity}
                                  </span>
                                )}
                                {vuln.port && (
                                  <span className="text-xs text-gray-600">
                                    Port: {vuln.port}
                                  </span>
                                )}
                              </div>
                              {vuln.solution && (
                                <p className="mt-2 text-xs text-gray-600">
                                  <strong>Solution:</strong> {vuln.solution}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No vulnerabilities found</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Exploitation Analysis</h3>
                  {scan.results.exploitation && scan.results.exploitation.findings?.length > 0 ? (
                    <div className="space-y-3">
                      <div className="bg-gray-900 text-green-400 p-3 rounded-lg mb-3">
                        <div><span className="text-green-600">Checks Performed:</span> {scan.results.exploitation.checks_performed}</div>
                      </div>
                      {scan.results.exploitation.findings.map((finding, idx) => (
                        <div key={idx} className={`p-3 rounded-lg border ${
                          finding.status === 'vulnerable' ? 'bg-red-50 border-red-200' :
                          finding.status === 'completed' ? 'bg-blue-50 border-blue-200' :
                          'bg-gray-50 border-gray-200'
                        }`}>
                          <div className="flex items-start gap-2">
                            <div className="flex-1">
                              <div className="font-medium text-sm">{finding.check}</div>
                              <div className="text-xs text-gray-600 mt-1">{finding.findings}</div>
                              {finding.severity && (
                                <span className={`inline-block mt-2 text-xs px-2 py-1 rounded ${
                                  finding.severity === 'critical' ? 'bg-red-100 text-red-800' :
                                  finding.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                                  'bg-yellow-100 text-yellow-800'
                                }`}>
                                  {finding.severity.toUpperCase()}
                                </span>
                              )}
                            </div>
                            <span className={`text-xs px-2 py-1 rounded ${
                              finding.status === 'vulnerable' ? 'bg-red-100 text-red-800' :
                              finding.status === 'completed' ? 'bg-green-100 text-green-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {finding.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No exploitation analysis data available</p>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'network' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Open Ports</h3>
                  {scan.results.open_ports?.length > 0 ? (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="space-y-2">
                        {scan.results.open_ports.map((port, index) => (
                          <div key={index} className="flex items-center justify-between py-2 border-b border-gray-200 last:border-0">
                            <div>
                              <span className="text-sm font-medium text-gray-900">Port {typeof port === 'object' ? port.port : port}</span>
                              {typeof port === 'object' && port.service && (
                                <span className="text-xs text-gray-500 ml-2">({port.service})</span>
                              )}
                            </div>
                            <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">
                              {typeof port === 'object' ? port.state : 'Open'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No open ports detected</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Footprinting Results</h3>
                  {scan.results.footprinting && Object.keys(scan.results.footprinting).length > 0 ? (
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      <div className="space-y-2">
                        {scan.results.footprinting.server && (
                          <div><span className="text-green-600">Server:</span> {scan.results.footprinting.server}</div>
                        )}
                        {scan.results.footprinting.technologies && (
                          <div><span className="text-green-600">Technologies:</span> {scan.results.footprinting.technologies.join(', ')}</div>
                        )}
                        {scan.results.footprinting.security_headers && (
                          <div>
                            <div className="text-green-600 mb-1">Security Headers:</div>
                            <div className="ml-4 space-y-1">
                              {Object.entries(scan.results.footprinting.security_headers).map(([key, value]) => (
                                <div key={key}>
                                  <span className={value ? 'text-green-400' : 'text-red-400'}>
                                    {key}: {value ? '✓ Present' : '✗ Missing'}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No footprinting data available</p>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'web' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Nikto Web Vulnerability Scan</h3>
                  {scan.results.nikto && Object.keys(scan.results.nikto).length > 0 ? (
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      <div className="space-y-2">
                        <div><span className="text-green-600">Target:</span> {scan.results.nikto.target}</div>
                        <div><span className="text-green-600">Server:</span> {scan.results.nikto.server}</div>
                        <div><span className="text-green-600">Issues Found:</span> {scan.results.nikto.issues_count || 0}</div>
                        {scan.results.nikto.findings && scan.results.nikto.findings.length > 0 && (
                          <div>
                            <div className="text-green-600 mt-2">Findings:</div>
                            <ul className="ml-4 mt-1 space-y-1 list-disc">
                              {scan.results.nikto.findings.map((finding, idx) => (
                                <li key={idx}>{finding}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No Nikto scan data available</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Directory Enumeration (Gobuster)</h3>
                  {scan.results.gobuster && scan.results.gobuster.paths?.length > 0 ? (
                    <div className="space-y-2">
                      <div className="bg-gray-900 text-green-400 p-4 rounded-lg mb-3">
                        <div><span className="text-green-600">Target:</span> {scan.results.gobuster.target}</div>
                        <div><span className="text-green-600">Paths Discovered:</span> {scan.results.gobuster.paths.length}</div>
                      </div>
                      <div className="space-y-2">
                        {scan.results.gobuster.paths.map((path, idx) => (
                          <div key={idx} className={`p-3 rounded-lg border ${
                            path.status >= 200 && path.status < 300 ? 'bg-green-50 border-green-200' :
                            path.status >= 400 && path.status < 500 ? 'bg-yellow-50 border-yellow-200' :
                            'bg-gray-50 border-gray-200'
                          }`}>
                            <div className="flex items-center justify-between">
                              <div className="font-mono text-sm">{path.path}</div>
                              <span className={`px-2 py-1 rounded text-xs ${
                                path.status >= 200 && path.status < 300 ? 'bg-green-100 text-green-800' :
                                path.status >= 400 && path.status < 500 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                Status {path.status}
                              </span>
                            </div>
                            {path.size && <div className="text-xs text-gray-600 mt-1">Size: {path.size}</div>}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No directories discovered</p>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'report' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-blue-900 mb-2 flex items-center">
                    <FileText className="h-5 w-5 mr-2" />
                    Professional Security Report
                  </h3>
                  <p className="text-sm text-blue-700">
                    Comprehensive penetration testing report following OWASP and PTES standards.
                  </p>
                </div>

                <div className="max-w-none">
                  {scan.results.ai_report ? (
                    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                      <div 
                        className="markdown-report p-8"
                        dangerouslySetInnerHTML={{
                          __html: (() => {
                            let html = scan.results.ai_report;
                            
                            // Replace emojis first
                            html = html.replace(/🔴/g, '<span class="text-red-600 font-bold">🔴</span>');
                            html = html.replace(/🟠/g, '<span class="text-orange-500 font-bold">🟠</span>');
                            html = html.replace(/🟡/g, '<span class="text-yellow-500 font-bold">🟡</span>');
                            html = html.replace(/🟢/g, '<span class="text-green-600 font-bold">🟢</span>');
                            html = html.replace(/✅/g, '<span class="text-green-600">✅</span>');
                            html = html.replace(/❌/g, '<span class="text-red-600">❌</span>');
                            html = html.replace(/⚠️/g, '<span class="text-yellow-600">⚠️</span>');
                            
                            // Replace code blocks
                            html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-blue-600">$1</code>');
                            
                            // Replace bold text (anywhere in line, not just start)
                            html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
                            
                            // Split by lines for processing
                            const lines = html.split('\n');
                            const processedLines = lines.map(line => {
                              // Skip empty lines
                              if (line.trim() === '') return '<br/>';
                              
                              // Headers
                              if (line.match(/^# /)) {
                                return line.replace(/^# (.*)$/, '<h1 class="text-3xl font-bold text-gray-900 mb-6 pb-4 border-b-2 border-blue-500">$1</h1>');
                              }
                              if (line.match(/^## /)) {
                                return line.replace(/^## (.*)$/, '<h2 class="text-2xl font-semibold text-gray-800 mt-8 mb-4 pb-2 border-b border-gray-300">$1</h2>');
                              }
                              if (line.match(/^### /)) {
                                return line.replace(/^### (.*)$/, '<h3 class="text-xl font-semibold text-gray-700 mt-6 mb-3">$1</h3>');
                              }
                              
                              // Horizontal rules
                              if (line.match(/^---+$/)) {
                                return '<hr class="my-8 border-t-2 border-gray-300" />';
                              }
                              
                              // Unordered lists
                              if (line.match(/^  - /)) {
                                return '<li class="ml-10 mb-1 text-gray-700 list-disc">' + line.replace(/^  - /, '') + '</li>';
                              }
                              if (line.match(/^- /)) {
                                return '<li class="ml-6 mb-2 text-gray-700 list-disc">' + line.replace(/^- /, '') + '</li>';
                              }
                              
                              // Ordered lists
                              if (line.match(/^[0-9]+\. /)) {
                                return '<li class="ml-6 mb-2 text-gray-700">' + line.replace(/^[0-9]+\. /, '') + '</li>';
                              }
                              
                              // Italic text (for emphasis)
                              line = line.replace(/\*([^*]+)\*/g, '<em class="italic text-gray-600">$1</em>');
                              
                              // Regular paragraph
                              return '<p class="mb-3 text-gray-700 leading-relaxed">' + line + '</p>';
                            });
                            
                            return processedLines.join('\n');
                          })()
                        }}
                      />
                      <style>{`
                        .markdown-report h1 {
                          color: #1e3a8a;
                          margin-top: 0;
                        }
                        .markdown-report h2 {
                          color: #1e40af;
                          scroll-margin-top: 2rem;
                        }
                        .markdown-report h3 {
                          color: #1e40af;
                          scroll-margin-top: 2rem;
                        }
                        .markdown-report li {
                          list-style-type: disc;
                          list-style-position: outside;
                          line-height: 1.6;
                        }
                        .markdown-report strong {
                          color: #111827;
                          font-weight: 600;
                        }
                        .markdown-report code {
                          background-color: #f3f4f6;
                          padding: 0.125rem 0.375rem;
                          border-radius: 0.25rem;
                          font-size: 0.875rem;
                          font-family: 'Courier New', monospace;
                        }
                        .markdown-report hr {
                          margin: 2rem 0;
                          border-color: #d1d5db;
                        }
                        .markdown-report p {
                          margin-bottom: 1rem;
                          line-height: 1.7;
                        }
                      `}</style>
                    </div>
                  ) : (
                    <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
                      <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-sm text-gray-500">Report not available</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ScanResults;
