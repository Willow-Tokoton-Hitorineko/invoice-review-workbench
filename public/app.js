"use strict";
const $=s=>document.querySelector(s), rowsEl=$('#rows'), message=$('#message');
let records=[], results=[], version=0, reviewedVersion=-1, busy=false, changed=false;
const labels={invoice_id:'编号',amount:'金额',currency:'币种',category:'科目',project:'项目',expense_date:'实际发生日期'};
const explanations={
'invoice_id is required':'请填写票据编号',
'duplicate invoice_id in this batch':'批次中编号重复，请核对票据事实',
'amount must be positive, finite and have at most two decimal places':'金额须为正数，且最多两位小数',
'explicit uppercase currency required':'币种须为三位大写字母，例如 CNY',
'category, project and actual expense_date require human confirmation':'补齐科目、项目、实际发生日期，并勾选本人确认',
'expense_date must be a valid ISO YYYY-MM-DD date':'发生日期须为有效日期（YYYY-MM-DD）'};
function payload(){return {invoices:records.map(r=>({invoice_id:r.invoice_id,amount:r.amount,currency:r.currency,...(r.issue_date?{issue_date:r.issue_date}:{}),human_approval:r.confirmed?{...r.approval}:{}}))}}
function summary(){
 const valid=reviewedVersion===version, count=valid?results.filter(r=>r.status==='APPROVED').length:0;
 $('#total').textContent=records.length+' 条票据';$('#approved').textContent=count+' 条通过';
 $('#pending').textContent=valid?(records.length-count)+' 条需要处理':'修改后请校验';
 $('#export').disabled=busy||!valid||!records.length||count!==records.length;
 $('#review').disabled=busy||!records.length;
 applyFilter();
}
function applyFilter(){let visible=0;[...rowsEl.children].forEach((tr,i)=>{tr.hidden=$('#statusFilter').value==='attention'&&reviewedVersion===version&&results[i]?.status==='APPROVED';if(!tr.hidden)visible++});$('#empty').hidden=visible>0}
function invalidate(){version++;reviewedVersion=-1;results=[];changed=true;rowsEl.querySelectorAll('.result').forEach(el=>{el.textContent='待校验';el.dataset.status=''});message.textContent='批次已修改，请重新确认修改行并校验。';summary()}
function replaceAllowed(){return !changed||window.confirm('重载或导入会替换当前未保存的批次，继续吗？')}
function makeField(record,key,index){const label=document.createElement('label');label.textContent=labels[key];const input=document.createElement('input');input.type=key==='expense_date'?'date':'text';if(key==='amount')input.inputMode='decimal';input.value=key in record?record[key]:record.approval[key]||'';input.setAttribute('aria-label','第 '+(index+1)+' 行'+labels[key]);input.oninput=()=>{if(key in record)record[key]=input.value;else record.approval[key]=input.value;record.confirmed=false;rowsEl.children[index].querySelector('[type=checkbox]').checked=false;invalidate()};label.append(input);return label}
function render(){rowsEl.replaceChildren();records.forEach((record,index)=>{
 const tr=document.createElement('tr'),fact=document.createElement('td'),human=document.createElement('td'),confirm=document.createElement('td'),actions=document.createElement('td');
 ['invoice_id','amount','currency'].forEach(k=>fact.append(makeField(record,k,index)));
 if(record.issue_date){const note=document.createElement('small');note.textContent='开票日期：'+record.issue_date+'（仅供参考）';fact.append(note)}
 ['category','project','expense_date'].forEach(k=>human.append(makeField(record,k,index)));
 const label=document.createElement('label');label.className='confirm';const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=record.confirmed;checkbox.setAttribute('aria-label','第 '+(index+1)+' 行本人确认');checkbox.onchange=()=>{record.confirmed=checkbox.checked;invalidate()};label.append(checkbox,document.createTextNode('本人确认'));confirm.append(label);
 const result=document.createElement('div');result.className='result';result.textContent='待校验';const remove=document.createElement('button');remove.type='button';remove.textContent='移除此行';remove.setAttribute('aria-label','移除第 '+(index+1)+' 行');remove.onclick=()=>{records.splice(index,1);invalidate();render()};actions.append(result,remove);tr.append(fact,human,confirm,actions);rowsEl.append(tr);
 });summary()}
function importRows(data){
 if(!data||!Array.isArray(data.invoices)||data.invoices.length>200)throw Error('请输入包含 invoices 数组的 JSON，最多 200 行');
 const next=data.invoices.map(r=>{
  if(!r||typeof r!=='object'||Array.isArray(r)||typeof r.invoice_id!=='string')throw Error('每行须为对象，并包含字符串 invoice_id');
  const a=r.human_approval??{};
  if(!a||typeof a!=='object'||Array.isArray(a)||Object.keys(a).some(k=>!['category','project','expense_date'].includes(k))||Object.values(a).some(v=>typeof v!=='string'))throw Error('human_approval 仅支持字符串 category、project、expense_date');
  if((typeof r.amount!=='string'&&typeof r.amount!=='number')||typeof r.currency!=='string')throw Error('请提供字符串/数字金额与字符串币种');
  return {invoice_id:r.invoice_id,amount:String(r.amount),currency:r.currency,issue_date:typeof r.issue_date==='string'?r.issue_date:'',approval:{category:a.category||'',project:a.project||'',expense_date:a.expense_date||''},confirmed:false};
 });records=next;invalidate();render();changed=false;message.textContent='已载入 '+records.length+' 行，请检查事实、补齐人工字段并逐行确认。';$('#input').value=JSON.stringify(payload(),null,2);
}
function setBusy(value){busy=value;$('#editor').disabled=value;$('#review').textContent=value?'处理中…':'校验整个批次';summary()}
async function send(path){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});if(!response.ok){let detail=await response.json();throw Error(detail.error||'请求失败（'+response.status+'）')}return response}
async function sample(){if(!replaceAllowed())return;setBusy(true);try{const r=await fetch('/sample');if(!r.ok)throw Error('示例载入失败');importRows(await r.json())}catch(e){message.textContent=e.message}finally{setBusy(false)}}
$('#sample').onclick=sample;
$('#add').onclick=()=>{if(records.length>=200){message.textContent='批次最多 200 行';return}records.push({invoice_id:'',amount:'',currency:'CNY',issue_date:'',approval:{category:'',project:'',expense_date:''},confirmed:false});invalidate();render();rowsEl.lastElementChild.querySelector('input').focus()};
$('#statusFilter').onchange=applyFilter;
$('#sync').onclick=()=>{$('#input').value=JSON.stringify(payload(),null,2);message.textContent='JSON 已同步为当前表格；未确认行的人工审批字段不提交。'};
$('#import').onclick=()=>{try{const data=JSON.parse($('#input').value);if(replaceAllowed())importRows(data)}catch(e){message.textContent='导入失败：'+e.message}};
$('#review').onclick=async()=>{setBusy(true);try{results=await(await send('/review')).json();reviewedVersion=version;results.forEach((r,i)=>{const el=rowsEl.children[i].querySelector('.result');el.dataset.status=r.status;el.textContent=({APPROVED:'已通过',REVIEW:'待复核',REJECT:'事实需修正'})[r.status]+'\n'+[...r.errors,...r.reasons].map(x=>explanations[x]||x).join('；')});message.textContent=results.every(r=>r.status==='APPROVED')?'全部通过，可以导出 CSV。':'校验完成。按每行提示处理后，重新确认与校验。'}catch(e){message.textContent=e.message;reviewedVersion=-1;results=[];rowsEl.querySelectorAll('.result').forEach(el=>{el.textContent='校验失败，请重试';el.dataset.status=''})}finally{setBusy(false)}};
$('#export').onclick=async()=>{if($('#export').disabled)return;setBusy(true);try{const blob=await(await send('/export')).blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='approved-invoices.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message.textContent='CSV 已导出；服务器未保存数据。'}catch(e){message.textContent=e.message}finally{setBusy(false)}};
sample();
