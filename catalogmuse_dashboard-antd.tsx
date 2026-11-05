import React, { useState } from 'react';
import { 
  Layout, 
  Steps, 
  Card, 
  Button, 
  Input, 
  Checkbox, 
  Select, 
  Tabs, 
  Tag, 
  Row, 
  Col, 
  Typography, 
  Space, 
  Badge, 
  Divider,
  Spin
} from 'antd';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Image as ImageIcon, 
  RefreshCcw, 
  Check, 
  ChevronRight, 
  Settings, 
  Wand2, 
  LayoutGrid, 
  ShieldCheck, 
  ShoppingBag, 
  ShoppingCart, 
  Plus, 
  MessageSquare 
} from 'lucide-react';

const { Header, Content } = Layout;
const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const STEPS = [
  { title: 'Intake' },
  { title: 'Cutout Approval' },
  { title: 'Lifestyle Gen' },
  { title: 'SEO & Compliance' },
  { title: 'Final Review' }
];

// --- Sub-components for Steps ---

const Step1Intake = ({ onNext }) => {
  const [marketplaces, setMarketplaces] = useState({ amazon: true, walmart: false });

  return (
    <Row gutter={[24, 24]}>
      {/* Left: Upload */}
      <Col xs={24} md={12}>
        <Card 
          title={
            <Space align="center">
              <ImageIcon style={{ color: '#6366f1' }} size={20} />
              <Text bold>Raw Supplier Image</Text>
            </Space>
          }
          style={{ height: '100%' }}
        >
          <div 
            style={{
              border: '2px dashed #d9d9d9',
              borderRadius: '8px',
              height: '260px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#fafafa',
              cursor: 'pointer',
              transition: 'all 0.3s'
            }}
          >
            <UploadCloud size={48} style={{ color: '#8c8c8c', marginBottom: '12px' }} />
            <Text type="secondary" style={{ fontSize: '14px', fontWeight: 500 }}>
              Drag & drop raw image here
            </Text>
            <Text type="secondary" style={{ fontSize: '12px', marginTop: '4px' }}>
              Supports JPG, PNG up to 10MB
            </Text>
          </div>
        </Card>
      </Col>

      {/* Right: Specs & Marketplaces */}
      <Col xs={24} md={12}>
        <Card 
          title={
            <Space align="center">
              <FileText style={{ color: '#6366f1' }} size={20} />
              <Text bold>Product Details</Text>
            </Space>
          }
          style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
          bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
        >
          <div>
            <div style={{ marginBottom: '16px' }}>
              <Text font-medium style={{ display: 'block', marginBottom: '8px' }}>Product Spec Sheet</Text>
              <TextArea 
                rows={4}
                placeholder="Paste raw supplier specs here (e.g., dimensions, materials, features)..."
                defaultValue="Blue silicone spatula, heat resistant up to 600F, ergonomic handle, dishwasher safe, 11 inches long. Made by KitchenPro."
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <Text style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Target Marketplaces</Text>
              <Row gutter={16}>
                <Col span={12}>
                  <Card 
                    size="small" 
                    hoverable 
                    style={{ borderColor: marketplaces.amazon ? '#6366f1' : '#d9d9d9' }}
                    onClick={() => setMarketplaces({ ...marketplaces, amazon: !marketplaces.amazon })}
                  >
                    <Space align="center">
                      <Checkbox checked={marketplaces.amazon} />
                      <ShoppingBag size={18} style={{ color: '#f97316' }} />
                      <Text style={{ fontWeight: 500 }}>Amazon</Text>
                    </Space>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card 
                    size="small" 
                    hoverable 
                    style={{ borderColor: marketplaces.walmart ? '#6366f1' : '#d9d9d9' }}
                    onClick={() => setMarketplaces({ ...marketplaces, walmart: !marketplaces.walmart })}
                  >
                    <Space align="center">
                      <Checkbox checked={marketplaces.walmart} />
                      <ShoppingCart size={18} style={{ color: '#3b82f6' }} />
                      <Text style={{ fontWeight: 500 }}>Walmart</Text>
                    </Space>
                  </Card>
                </Col>
              </Row>
            </div>
          </div>

          <Button 
            type="primary" 
            size="large" 
            icon={<Wand2 size={16} />} 
            onClick={onNext}
            block
            style={{ backgroundColor: '#4f46e5', borderColor: '#4f46e5', height: '44px' }}
          >
            Generate Agentic Cutout
          </Button>
        </Card>
      </Col>
    </Row>
  );
};

const Step2Cutout = ({ onNext, onBack }) => {
  const [showRecut, setShowRecut] = useState(false);
  const [recutPrompt, setRecutPrompt] = useState('');

  return (
    <Card 
      title={
        <Space align="center">
          <CheckCircle style={{ color: '#6366f1' }} size={22} />
          <Title level={4} style={{ margin: 0 }}>Agentic Segmentation Review</Title>
        </Space>
      }
    >
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        {/* Raw Image Mock */}
        <Col xs={24} md={12}>
          <Text strong style={{ display: 'block', marginBottom: '8px' }}>Original Supplier Photo</Text>
          <div 
            style={{
              aspectRatio: '1 / 1',
              backgroundColor: '#e2e8f0',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <div style={{ position: 'absolute', inset: 0, opacity: 0.5, backgroundImage: `radial-gradient(#cbd5e1 1px, transparent 1px)`, backgroundSize: '16px 16px' }} />
            <div style={{ width: '128px', height: '192px', backgroundColor: '#3b82f6', borderTopLeftRadius: '9999px', borderTopRightRadius: '9999px', borderBottomLeftRadius: '6px', borderBottomRightRadius: '6px', transform: 'rotate(12deg)', position: 'relative', zIndex: 1, boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
          </div>
        </Col>

        {/* Cutout Mock */}
        <Col xs={24} md={12}>
          <Text strong style={{ display: 'block', marginBottom: '8px' }}>SAM 3.1 Transparent Cutout</Text>
          <div 
            style={{
              aspectRatio: '1 / 1',
              backgroundColor: '#f8fafc',
              backgroundImage: 'linear-gradient(45deg, #e2e8f0 25%, transparent 25%), linear-gradient(-45deg, #e2e8f0 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #e2e8f0 75%), linear-gradient(-45deg, transparent 75%, #e2e8f0 75%)',
              backgroundSize: '20px 20px',
              backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid #e2e8f0'
            }}
          >
            <div style={{ width: '128px', height: '192px', backgroundColor: '#3b82f6', borderTopLeftRadius: '9999px', borderTopRightRadius: '9999px', borderBottomLeftRadius: '6px', borderBottomRightRadius: '6px', transform: 'rotate(12deg)', filter: 'drop-shadow(0 20px 13px rgba(0,0,0,0.15))' }} />
          </div>
        </Col>
      </Row>

      <Divider style={{ margin: '16px 0 24px' }} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Button onClick={onBack} type="text">Cancel</Button>
        
        <Space>
          {showRecut ? (
            <Space>
              <Input 
                prefix={<MessageSquare size={16} style={{ color: '#bfbfbf' }} />}
                placeholder="Instruct the AI (e.g., remove reflection)..."
                value={recutPrompt}
                onChange={(e) => setRecutPrompt(e.target.value)}
                style={{ width: '280px' }}
                autoFocus
              />
              <Button 
                type="primary" 
                style={{ backgroundColor: '#1e293b' }}
                onClick={() => {
                  setShowRecut(false);
                  setRecutPrompt('');
                }}
              >
                Submit Recut
              </Button>
              <Button type="text" onClick={() => setShowRecut(false)}>✕</Button>
            </Space>
          ) : (
            <>
              <Button icon={<RefreshCcw size={16} />} onClick={() => setShowRecut(true)}>
                Recut
              </Button>
              <Button type="primary" icon={<Check size={16} />} style={{ backgroundColor: '#4f46e5' }} onClick={onNext}>
                Approve Cutout
              </Button>
            </>
          )}
        </Space>
      </div>
    </Card>
  );
};

const Step3Lifestyle = ({ onNext, onBack, approvedImages, setApprovedImages }) => {
  const [aesthetics, setAesthetics] = useState([
    'Modern Minimalist Kitchen, bright morning light, 8k resolution',
    'Rustic Family Dining Table, warm tones, lifestyle photography',
    'Bright Studio Lighting, solid white background with soft subtle shadow'
  ]);
  const [selectedAesthetics, setSelectedAesthetics] = useState([0, 1, 2]);
  const [variationsCount, setVariationsCount] = useState(4);
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);

  const toggleAesthetic = (index) => {
    if (selectedAesthetics.includes(index)) {
      setSelectedAesthetics(selectedAesthetics.filter(i => i !== index));
    } else {
      setSelectedAesthetics([...selectedAesthetics, index]);
    }
  };

  const updateAesthetic = (index, value) => {
    const newAesthetics = [...aesthetics];
    newAesthetics[index] = value;
    setAesthetics(newAesthetics);
  };

  const addAesthetic = () => {
    setAesthetics([...aesthetics, '']);
    setSelectedAesthetics([...selectedAesthetics, aesthetics.length]);
  };

  const handleGenerate = () => {
    setGenerating(true);
    setApprovedImages({});
    setTimeout(() => {
      setGenerating(false);
      setGenerated(true);
    }, 1500);
  };

  const toggleApprove = (styleIndex, varIndex) => {
    const key = `${styleIndex}-${varIndex}`;
    setApprovedImages(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const hasApproval = Object.values(approvedImages).some(Boolean);

  return (
    <Space direction="vertical" size={24} style={{ width: '100%' }}>
      <Card 
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <Space align="center">
              <LayoutGrid size={20} style={{ color: '#6366f1' }} />
              <Text bold style={{ fontSize: '16px' }}>Art Director Agent Options</Text>
            </Space>
            <Space align="center" style={{ backgroundColor: '#f8fafc', padding: '4px 12px', borderRadius: '6px', border: '1px solid #f1f5f9' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>Variations per style:</Text>
              <Select 
                value={variationsCount} 
                onChange={setVariationsCount} 
                bordered={false} 
                options={[
                  { value: 4, label: '4 Variations' },
                  { value: 3, label: '3 Variations' },
                  { value: 2, label: '2 Variations' },
                  { value: 1, label: '1 Variation' }
                ]}
              />
            </Space>
          </div>
        }
      >
        <Text type="secondary" style={{ display: 'block', marginBottom: '16px' }}>
          Select and edit the suggested prompts below, or add your own custom style.
        </Text>

        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          {aesthetics.map((aesthetic, i) => {
            const isChecked = selectedAesthetics.includes(i);
            return (
              <Col xs={24} md={12} key={i}>
                <Card 
                  size="small"
                  style={{ 
                    borderColor: isChecked ? '#6366f1' : '#e2e8f0', 
                    backgroundColor: isChecked ? '#f5f3ff' : '#ffffff' 
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', cursor: 'pointer' }} onClick={() => toggleAesthetic(i)}>
                    <Checkbox checked={isChecked} />
                    <Text uppercase style={{ fontSize: '11px', fontWeight: 600, color: '#475569' }}>Style {i + 1}</Text>
                  </div>
                  <TextArea 
                    value={aesthetic}
                    onChange={(e) => updateAesthetic(i, e.target.value)}
                    placeholder="Describe the aesthetic prompt..."
                    rows={2}
                    style={{ backgroundColor: 'transparent', border: 'none' }}
                  />
                </Card>
              </Col>
            );
          })}

          <Col xs={24} md={12}>
            <div 
              onClick={addAesthetic}
              style={{
                border: '2px dashed #cbd5e1',
                borderRadius: '8px',
                height: '100%',
                minHeight: '100px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: '#64748b',
                transition: 'all 0.3s'
              }}
            >
              <Plus size={24} />
              <Text style={{ fontSize: '14px', fontWeight: 500, color: '#64748b' }}>Add Custom Style</Text>
            </div>
          </Col>
        </Row>

        <Button 
          type="primary" 
          size="large" 
          block 
          onClick={handleGenerate}
          disabled={generating || selectedAesthetics.length === 0}
          icon={generating ? <Spin size="small" /> : <Wand2 size={16} />}
          style={{ backgroundColor: '#0f172a', borderColor: '#0f172a', height: '44px' }}
        >
          {generating ? 'Muse Image is Generating...' : `Generate ${selectedAesthetics.length * variationsCount} Images`}
        </Button>
      </Card>

      {generated && (
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          {selectedAesthetics.map((styleIndex) => (
            <Card 
              key={styleIndex} 
              title={
                <div>
                  <Text strong style={{ fontSize: '16px' }}>Style {styleIndex + 1}</Text>
                  <Paragraph type="secondary" italic style={{ margin: '4px 0 0', fontSize: '12px', background: '#f8fafc', padding: '4px 8px', borderRadius: '4px' }}>
                    "{aesthetics[styleIndex] || 'Custom Style'}"
                  </Paragraph>
                </div>
              }
            >
              <Row gutter={[16, 16]}>
                {Array.from({ length: variationsCount }).map((_, varIndex) => {
                  const key = `${styleIndex}-${varIndex}`;
                  const isApproved = !!approvedImages[key];

                  return (
                    <Col xs={24} sm={12} md={6} key={varIndex}>
                      <div 
                        onClick={() => toggleApprove(styleIndex, varIndex)}
                        style={{
                          borderRadius: '8px',
                          overflow: 'hidden',
                          border: `2px solid ${isApproved ? '#22c55e' : '#e2e8f0'}`,
                          position: 'relative',
                          cursor: 'pointer',
                          transition: 'all 0.2s'
                        }}
                      >
                        <div style={{ aspectRatio: '4/5', backgroundColor: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                          <div style={{ width: '64px', height: '96px', backgroundColor: '#3b82f6', borderTopLeftRadius: '9999px', borderTopRightRadius: '9999px', transform: 'rotate(12deg)' }} />
                          {styleIndex % 2 === 0 ? (
                            <div style={{ position: 'absolute', bottom: 0, width: '100%', height: '33%', backgroundColor: '#cbd5e1' }} />
                          ) : (
                            <div style={{ position: 'absolute', bottom: 0, width: '100%', height: '25%', backgroundColor: 'rgba(146, 64, 14, 0.2)' }} />
                          )}
                        </div>

                        {isApproved && (
                          <div style={{ position: 'absolute', top: 8, right: 8, backgroundColor: '#22c55e', color: '#fff', borderRadius: '50%', padding: '4px' }}>
                            <Check size={14} />
                          </div>
                        )}
                      </div>
                    </Col>
                  );
                })}
              </Row>
            </Card>
          ))}

          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Button onClick={onBack}>Back</Button>
              <Space size={16}>
                <Text type="secondary" style={{ fontWeight: 500 }}>
                  {Object.keys(approvedImages).filter(k => approvedImages[k]).length} approved
                </Text>
                <Button 
                  type="primary" 
                  disabled={!hasApproval}
                  onClick={onNext}
                  icon={<ChevronRight size={16} />}
                  style={{ backgroundColor: hasApproval ? '#4f46e5' : undefined }}
                >
                  Next Step
                </Button>
              </Space>
            </div>
          </Card>
        </Space>
      )}
    </Space>
  );
};

const Step4SEO = ({ onNext, onBack }) => {
  const [activeTab, setActiveTab] = useState('amazon');

  const tabItems = [
    {
      key: 'amazon',
      label: <span style={{ color: activeTab === 'amazon' ? '#f97316' : undefined }}>Amazon Listing</span>,
      children: (
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Text strong style={{ display: 'block', marginBottom: '4px' }}>Product Title</Text>
            <Input 
              defaultValue="KitchenPro Premium Silicone Spatula - 11 Inch Heat Resistant (600°F) Non-Stick Rubber Spatula for Baking, Cooking, and Mixing, Dishwasher Safe (Ocean Blue)"
            />
          </div>
          <div>
            <Text strong style={{ display: 'block', marginBottom: '4px' }}>Key Features (Bullet Points)</Text>
            <TextArea 
              rows={5}
              defaultValue={`• HIGH HEAT RESISTANCE: Engineered to withstand temperatures up to 600°F without melting or warping.\n• SEAMLESS DESIGN: One-piece construction ensures no food gets trapped, making it hygienic and easy to clean.\n• ERGONOMICS: Soft grip handle provides comfortable control for stirring, scraping, and folding.`}
            />
          </div>
          <div>
            <Text strong style={{ display: 'block', marginBottom: '4px' }}>Product Description</Text>
            <TextArea 
              rows={3}
              defaultValue="Upgrade your kitchen essentials with the KitchenPro Silicone Spatula. Designed for home chefs and bakers, this 11-inch spatula features a seamless, one-piece construction that is both durable and easy to clean."
            />
          </div>
        </Space>
      )
    },
    {
      key: 'walmart',
      label: <span style={{ color: activeTab === 'walmart' ? '#3b82f6' : undefined }}>Walmart Listing</span>,
      children: (
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Text strong style={{ display: 'block', marginBottom: '4px' }}>Product Title</Text>
            <Input 
              defaultValue="KitchenPro Silicone Spatula, 11-Inch, Heat Resistant, Ocean Blue"
            />
          </div>
          <div>
            <Text strong style={{ display: 'block', marginBottom: '4px' }}>Key Features (Bullet Points)</Text>
            <TextArea 
              rows={5}
              defaultValue={`<ul>\n  <li>Heat resistant up to 600 degrees Fahrenheit</li>\n  <li>Seamless one-piece silicone design</li>\n  <li>Dishwasher safe for easy cleanup</li>\n</ul>`}
            />
          </div>
          <div>
            <Text strong style={{ display: 'block', marginBottom: '4px' }}>Product Description</Text>
            <TextArea 
              rows={3}
              defaultValue="Upgrade your kitchen essentials with the KitchenPro Silicone Spatula. Designed for home chefs and bakers..."
            />
          </div>
        </Space>
      )
    }
  ];

  return (
    <Row gutter={[24, 24]}>
      <Col xs={24} lg={16}>
        <Card bodyStyle={{ padding: '12px 24px 24px' }}>
          <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
        </Card>
      </Col>

      <Col xs={24} lg={8}>
        <Card 
          style={{ backgroundColor: '#0f172a', color: '#cbd5e1', border: '1px solid #1e293b', height: '100%' }}
          bodyStyle={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '12px' }}>
              <Space>
                <ShieldCheck size={18} style={{ color: '#818cf8' }} />
                <Text style={{ color: '#818cf8', fontWeight: 600 }}>Muse Spark Auditor</Text>
              </Space>
              <Badge status="processing" color="#22c55e" />
            </div>

            <Space direction="vertical" size={12} style={{ width: '100%', fontFamily: 'monospace', fontSize: '13px' }}>
              {activeTab === 'amazon' ? (
                <>
                  <Space align="start">
                    <CheckCircle size={16} style={{ color: '#4ade80', marginTop: '2px' }} />
                    <Text style={{ color: '#4ade80' }}>Amazon TOS rules loaded.</Text>
                  </Space>
                  <Space align="start">
                    <AlertCircle size={16} style={{ color: '#facc15', marginTop: '2px' }} />
                    <Text style={{ color: '#facc15' }}>Violation found: Removed "Best Seller" from Title draft.</Text>
                  </Space>
                  <Space align="start">
                    <CheckCircle size={16} style={{ color: '#4ade80', marginTop: '2px' }} />
                    <Text style={{ color: '#4ade80' }}>Title length check: 132 chars (Pass)</Text>
                  </Space>
                  <Space align="start">
                    <CheckCircle size={16} style={{ color: '#4ade80', marginTop: '2px' }} />
                    <Text style={{ color: '#4ade80' }}>Draft complies 100% with Amazon TOS.</Text>
                  </Space>
                </>
              ) : (
                <>
                  <Space align="start">
                    <CheckCircle size={16} style={{ color: '#4ade80', marginTop: '2px' }} />
                    <Text style={{ color: '#4ade80' }}>Walmart Item Setup rules loaded.</Text>
                  </Space>
                  <Space align="start">
                    <AlertCircle size={16} style={{ color: '#facc15', marginTop: '2px' }} />
                    <Text style={{ color: '#facc15' }}>Formatting: Converted bullets to HTML unordered list.</Text>
                  </Space>
                  <Space align="start">
                    <CheckCircle size={16} style={{ color: '#4ade80', marginTop: '2px' }} />
                    <Text style={{ color: '#4ade80' }}>Description length check: 450 chars (Pass)</Text>
                  </Space>
                </>
              )}
            </Space>
          </div>

          <div style={{ borderTop: '1px solid #1e293b', paddingTop: '16px', display: 'flex', gap: '8px', marginTop: '24px' }}>
            <Button onClick={onBack} style={{ color: '#94a3b8', borderColor: '#334155', backgroundColor: 'transparent' }}>
              Back
            </Button>
            <Button type="primary" onClick={onNext} block style={{ backgroundColor: '#4f46e5' }}>
              Approve Copy
            </Button>
          </div>
        </Card>
      </Col>
    </Row>
  );
};

const Step5Review = ({ onRestart, approvedImages }) => {
  const [activeTab, setActiveTab] = useState('amazon');
  const approvedKeys = Object.keys(approvedImages || {}).filter(k => approvedImages[k]);

  return (
    <Card bodyStyle={{ padding: 0 }}>
      <div style={{ background: 'linear-gradient(to right, #4f46e5, #2563eb)', padding: '24px', textAlign: 'center', color: '#fff' }}>
        <Space align="center" size={8} style={{ marginBottom: '8px' }}>
          <CheckCircle size={28} />
          <Title level={3} style={{ color: '#fff', margin: 0 }}>Ready for Marketplace</Title>
        </Space>
        <Text style={{ color: '#e0e7ff' }}>All assets have passed Human-in-the-Loop approval.</Text>
      </div>

      <div style={{ padding: '24px' }}>
        <Row gutter={[32, 32]}>
          <Col xs={24} md={10}>
            <Title level={5} style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: '8px' }}>
              Approved Visuals ({approvedKeys.length})
            </Title>
            <Row gutter={[12, 12]}>
              {approvedKeys.length > 0 ? (
                approvedKeys.map((key, index) => {
                  const [styleIndex, varIndex] = key.split('-');
                  return (
                    <Col span={index === 0 ? 24 : 12} key={key}>
                      <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', aspectRatio: index === 0 ? '4/3' : '1/1', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <div style={{ width: '48px', height: '72px', backgroundColor: '#3b82f6', borderTopLeftRadius: '9999px', transform: 'rotate(6deg)' }} />
                        {index === 0 && (
                          <Tag color="green" icon={<Check size={12} />} style={{ position: 'absolute', top: 8, right: 8 }}>
                            Primary
                          </Tag>
                        )}
                        <Tag style={{ position: 'absolute', bottom: 4, right: 4, fontSize: '10px' }}>
                          Style {parseInt(styleIndex) + 1} - V{parseInt(varIndex) + 1}
                        </Tag>
                      </div>
                    </Col>
                  );
                })
              ) : (
                <Col span={24}>
                  <Text type="secondary">No images approved</Text>
                </Col>
              )}
            </Row>
          </Col>

          <Col xs={24} md={14}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f0f0f0', paddingBottom: '8px' }}>
              <Title level={5} style={{ margin: 0 }}>Approved Copy</Title>
              <Tag color="green" icon={<ShieldCheck size={12} />}>TOS Compliant</Tag>
            </div>

            <Tabs 
              activeKey={activeTab} 
              onChange={setActiveTab}
              items={[
                { key: 'amazon', label: 'Amazon Listing' },
                { key: 'walmart', label: 'Walmart Listing' }
              ]} 
            />

            <div style={{ backgroundColor: '#fafafa', padding: '16px', borderRadius: '8px', border: '1px solid #f0f0f0', marginBottom: '24px' }}>
              {activeTab === 'amazon' ? (
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary" style={{ fontSize: '11px', textTransform: 'uppercase', fontWeight: 600 }}>Final Title (Amazon)</Text>
                    <Paragraph strong style={{ margin: '4px 0 0' }}>KitchenPro Premium Silicone Spatula - 11 Inch Heat Resistant (600°F) Non-Stick Rubber Spatula for Baking and Mixing</Paragraph>
                  </div>
                  <Divider style={{ margin: '8px 0' }} />
                  <div>
                    <Text type="secondary" style={{ fontSize: '11px', textTransform: 'uppercase', fontWeight: 600 }}>Final Bullets</Text>
                    <ul style={{ paddingLeft: '20px', margin: '4px 0 0' }}>
                      <li><strong>HIGH HEAT RESISTANCE:</strong> Engineered to withstand temperatures up to 600°F.</li>
                      <li><strong>SEAMLESS DESIGN:</strong> One-piece construction ensures no food gets trapped.</li>
                      <li><strong>ERGONOMICS:</strong> Soft grip handle provides comfortable control.</li>
                    </ul>
                  </div>
                </Space>
              ) : (
                <div>
                  <Text type="secondary" style={{ fontSize: '11px', textTransform: 'uppercase', fontWeight: 600 }}>Final Title (Walmart)</Text>
                  <Paragraph strong style={{ margin: '4px 0 0' }}>KitchenPro Silicone Spatula, 11-Inch, Heat Resistant, Ocean Blue</Paragraph>
                </div>
              )}
            </div>

            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Button onClick={onRestart}>Start New Product</Button>
              <Button type="primary" size="large" icon={<UploadCloud size={18} />} style={{ backgroundColor: '#16a34a', borderColor: '#16a34a' }}>
                Publish to Catalog
              </Button>
            </Space>
          </Col>
        </Row>
      </div>
    </Card>
  );
};

// --- Main App Component ---

export default function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [approvedImages, setApprovedImages] = useState({});

  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1));
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0));
  const restart = () => {
    setCurrentStep(0);
    setApprovedImages({});
  };

  return (
    <Layout style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      <Header style={{ backgroundColor: '#ffffff', borderBottom: '1px solid #f0f0f0', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Space align="center" size={12}>
          <div style={{ backgroundColor: '#4f46e5', padding: '6px', borderRadius: '8px', display: 'flex' }}>
            <Wand2 size={20} style={{ color: '#fff' }} />
          </div>
          <Title level={4} style={{ margin: 0 }}>CatalogMuse</Title>
        </Space>
        <Space size={16}>
          <Tag color="blue">Beta 1.0</Tag>
          <Button type="text" icon={<Settings size={18} />} />
        </Space>
      </Header>

      <Content style={{ maxWidth: '1140px', width: '100%', margin: '0 auto', padding: '32px 24px' }}>
        <Card style={{ marginBottom: '24px' }}>
          <Steps 
            current={currentStep} 
            items={STEPS}
            onChange={(step) => setCurrentStep(step)}
          />
        </Card>

        <div>
          {currentStep === 0 && <Step1Intake onNext={nextStep} />}
          {currentStep === 1 && <Step2Cutout onNext={nextStep} onBack={prevStep} />}
          {currentStep === 2 && <Step3Lifestyle onNext={nextStep} onBack={prevStep} approvedImages={approvedImages} setApprovedImages={setApprovedImages} />}
          {currentStep === 3 && <Step4SEO onNext={nextStep} onBack={prevStep} />}
          {currentStep === 4 && <Step5Review onRestart={restart} approvedImages={approvedImages} />}
        </div>
      </Content>
    </Layout>
  );
}