const element=(tag,text,className='')=>Object.assign(document.createElement(tag),{textContent:text,className});
function external(container,url,label) {
  const link=element('a',label,'external-link');link.href=url;link.target='_blank';link.rel='noopener noreferrer';
  const notice=element('p',navigator.onLine?'Opens a new tab. YouTube and Google Forms require Internet access.':'Offline: local assignments work; YouTube and Google Forms require Internet access.','link-notice');
  link.addEventListener('click',event=>{if(!navigator.onLine){event.preventDefault();notice.textContent='Offline: connect to the Internet to open this external service. Your challenge is retained.';}});
  container.append(link,notice);
}
export function questionContents(container,unit,question,onChoose) {
  container.replaceChildren(element('p',`${unit.unitId} · ${unit.title}`,'unit-context'));
  external(container,question.questionVideoUrl,'Open English question video ↗');
  const answers=element('div','','answer-choices');
  question.options.forEach((option,index)=>{
    const label='ABCD'[index],button=element('button',`${label} · ${option}`,'answer-choice');
    button.type='button';button.dataset.answer=label;button.addEventListener('click',()=>onChoose(label));answers.append(button);
  });
  container.append(answers,element('p','Choose one answer. A wrong answer clears all progress and starts a smaller maze.','link-notice'));
}
export function correctContents(container,question) {
  container.replaceChildren(element('p',question.explanationText||'','explanation'));
  external(container,question.explanationVideoUrl,'Optional English explanation video ↗');
}
export function finishContents(container,unit,attempt) {
  container.replaceChildren(element('p',`${unit.unitId} · ${unit.title}`,'unit-context'),
    element('p',`${attempt.completed.filter(Boolean).length} / ${unit.questions.length} questions completed · Attempt ${attempt.failures+1}`));
  external(container,unit.googleFormUrl,'Open Google Form ↗');
}
