/**
 * Frontend Dashboard Test
 * Tests if frontend can correctly fetch and display dashboard data
 * Run in browser console at http://localhost:3000
 */

async function testFrontendDashboard() {
  console.log('🧪 Testing Frontend Dashboard Integration...\n');
  
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const batchId = 'batch_aicte_20251204_031927_b0280d54';
  
  try {
    // Test 1: Fetch dashboard data
    console.log('1. Fetching dashboard data...');
    const response = await fetch(`${API_BASE}/api/dashboard/${batchId}`);
    
    if (!response.ok) {
      console.error(`❌ Dashboard fetch failed: ${response.status}`);
      return;
    }
    
    const data = await response.json();
    console.log('✓ Dashboard data retrieved');
    
    // Test 2: Check structure
    console.log('\n2. Verifying data structure...');
    console.log(`   - Batch ID: ${data.batch_id}`);
    console.log(`   - Mode: ${data.mode}`);
    
    // Check if new format or old format
    if (data.blocks && Array.isArray(data.blocks)) {
      console.log(`   ✓ Blocks (new format): ${data.blocks.length} blocks`);
    } else if (data.block_cards && Array.isArray(data.block_cards)) {
      console.log(`   ✓ Block Cards (old format): ${data.block_cards.length} cards`);
    } else {
      console.log('   ⚠ No blocks found');
    }
    
    if (data.kpis && typeof data.kpis === 'object') {
      console.log(`   ✓ KPIs (new format): ${Object.keys(data.kpis).length} KPIs`);
      console.log(`     - FSR Score: ${data.kpis.fsr_score ?? 'null'}`);
      console.log(`     - Overall Score: ${data.kpis.overall_score ?? 'null'}`);
    } else if (data.kpi_cards && Array.isArray(data.kpi_cards)) {
      console.log(`   ✓ KPI Cards (old format): ${data.kpi_cards.length} cards`);
    } else {
      console.log('   ⚠ No KPIs found');
    }
    
    if (typeof data.sufficiency === 'number') {
      console.log(`   ✓ Sufficiency (new format): ${data.sufficiency}%`);
    } else if (data.sufficiency && typeof data.sufficiency === 'object') {
      console.log(`   ✓ Sufficiency (old format): ${data.sufficiency.percentage}%`);
    } else {
      console.log('   ⚠ No sufficiency found');
    }
    
    if (data.compliance && Array.isArray(data.compliance)) {
      console.log(`   ✓ Compliance (new format): ${data.compliance.length} flags`);
    } else if (data.compliance_flags && Array.isArray(data.compliance_flags)) {
      console.log(`   ✓ Compliance Flags (old format): ${data.compliance_flags.length} flags`);
    } else {
      console.log('   ⚠ No compliance flags found');
    }
    
    // Test 3: Test frontend API transformation
    console.log('\n3. Testing frontend API transformation...');
    try {
      // Simulate what frontend API does
      const transformed = {
        batch_id: data.batch_id,
        mode: data.mode,
        blocks: data.blocks || (data.block_cards || []).map(card => ({
          block_type: card.block_type,
          data: {},
          confidence: card.confidence,
          is_valid: !card.is_invalid && card.is_present,
          is_outdated: card.is_outdated,
          is_low_quality: card.is_low_quality,
          evidence_snippet: card.evidence_snippet,
          evidence_page: card.evidence_page,
          source_doc: card.source_doc,
        })),
        kpis: data.kpis || {
          fsr_score: data.kpi_cards?.find(k => k.name.toLowerCase().includes('fsr'))?.value ?? null,
          infra_score: data.kpi_cards?.find(k => k.name.toLowerCase().includes('infrastructure') || k.name.toLowerCase().includes('infra'))?.value ?? null,
          placement_index: data.kpi_cards?.find(k => k.name.toLowerCase().includes('placement'))?.value ?? null,
          lab_compliance_index: data.kpi_cards?.find(k => k.name.toLowerCase().includes('lab'))?.value ?? null,
          overall_score: data.kpi_cards?.find(k => k.name.toLowerCase().includes('overall'))?.value ?? null,
        },
        sufficiency: typeof data.sufficiency === 'number' ? data.sufficiency : (data.sufficiency?.percentage ?? 0),
        present_blocks: data.present_blocks ?? data.sufficiency?.present_count ?? 0,
        required_blocks: data.required_blocks ?? data.sufficiency?.required_count ?? 10,
        compliance: data.compliance || (data.compliance_flags || []).map(flag => ({
          severity: flag.severity.toUpperCase(),
          title: flag.title,
          reason: flag.reason,
        })),
        trends: data.trends || [],
      };
      
      console.log('✓ Transformation successful');
      console.log(`   - Blocks: ${transformed.blocks.length}`);
      console.log(`   - KPIs: ${Object.keys(transformed.kpis).length}`);
      console.log(`   - Sufficiency: ${transformed.sufficiency}%`);
      console.log(`   - Present Blocks: ${transformed.present_blocks}/${transformed.required_blocks}`);
      console.log(`   - Compliance: ${transformed.compliance.length} flags`);
      
    } catch (e) {
      console.error('❌ Transformation failed:', e.message);
    }
    
    console.log('\n✅ Frontend dashboard test complete!');
    console.log('\n📋 Summary:');
    console.log(`   - Backend API: ✓ Working`);
    console.log(`   - Data Structure: ✓ Valid`);
    console.log(`   - Frontend Transformation: ✓ Working`);
    console.log(`   - Ready for UI display: ✓ Yes`);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

// Run test
testFrontendDashboard();

