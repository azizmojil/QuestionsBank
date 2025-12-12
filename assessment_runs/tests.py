from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from assessment_flow.models import AssessmentQuestion, AssessmentFlowRule
import json

User = get_user_model()


class RewindAssessmentTestCase(TestCase):
    """Test cases for the rewind_assessment view to ensure proper backtracking behavior."""

    def setUp(self):
        """Set up test questions, rules, and client."""
        self.client = Client()
        
        # Create test questions
        self.q1 = AssessmentQuestion.objects.create(text="Question 1")
        self.q2 = AssessmentQuestion.objects.create(text="Question 2")
        self.q3 = AssessmentQuestion.objects.create(text="Question 3")
        
        # Create rules
        self.rule_a = AssessmentFlowRule.objects.create(
            from_question=self.q2,
            condition=f'{{"conditions": [{{"question": {self.q1.id}, "operator": "==", "value": "Yes"}}]}}',
            priority=1,
            is_active=True,
            description="Rule A"
        )
        
        self.rule_b = AssessmentFlowRule.objects.create(
            from_question=self.q3,
            condition=f'{{"conditions": [{{"question": {self.q2.id}, "operator": "==", "value": "Option1"}}]}}',
            priority=1,
            is_active=True,
            description="Rule B"
        )

    def test_rewind_preserves_rule_id(self):
        """Test that rewinding to a question preserves its rule_id."""
        session = self.client.session
        
        # Simulate a history where we've gone from Q1 -> Q2 -> Q3
        session['assessment_history'] = [
            {'question_id': self.q1.id, 'rule_id': None, 'answer': 'Yes'},
            {'question_id': self.q2.id, 'rule_id': self.rule_a.id, 'answer': 'Option1'},
            {'question_id': self.q3.id, 'rule_id': self.rule_b.id, 'answer': 'Continue'}
        ]
        session.save()
        
        # Rewind to Q2
        response = self.client.post(
            reverse('rewind_assessment'),
            data=json.dumps({'question_id': self.q2.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check the history after rewind
        history = self.client.session['assessment_history']
        
        # History should be truncated to Q1 and Q2
        self.assertEqual(len(history), 2)
        
        # Q2 should still have its rule_id (Rule A) preserved
        q2_entry = history[1]
        self.assertEqual(q2_entry['question_id'], self.q2.id)
        self.assertEqual(q2_entry['rule_id'], self.rule_a.id)
        
        # Q2's answer should be cleared
        self.assertNotIn('answer', q2_entry)

    def test_rewind_removes_subsequent_questions(self):
        """Test that rewinding removes all questions after the rewind point."""
        session = self.client.session
        
        # Simulate a history with Q1 -> Q2 -> Q3
        session['assessment_history'] = [
            {'question_id': self.q1.id, 'rule_id': None, 'answer': 'Yes'},
            {'question_id': self.q2.id, 'rule_id': self.rule_a.id, 'answer': 'Option1'},
            {'question_id': self.q3.id, 'rule_id': self.rule_b.id, 'answer': 'Continue'}
        ]
        session.save()
        
        # Rewind to Q1
        response = self.client.post(
            reverse('rewind_assessment'),
            data=json.dumps({'question_id': self.q1.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check the history after rewind
        history = self.client.session['assessment_history']
        
        # History should only contain Q1
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['question_id'], self.q1.id)
        
        # Q1's answer should be cleared
        self.assertNotIn('answer', history[0])

    def test_get_next_question_uses_correct_used_rules(self):
        """Test that get_next_question_view correctly identifies used rules after rewind."""
        session = self.client.session
        
        # Simulate a history where we've rewound to Q2
        # Q1 -> Q2 (via Rule A), and Q3 was removed
        session['assessment_history'] = [
            {'question_id': self.q1.id, 'rule_id': None, 'answer': 'Yes'},
            {'question_id': self.q2.id, 'rule_id': self.rule_a.id}  # No answer yet (just rewound)
        ]
        session.save()
        
        # Submit a new answer for Q2
        response = self.client.post(
            reverse('get_next_question'),
            data=json.dumps({
                'question_id': self.q2.id,
                'option_ids': ['test_option']
            }),
            content_type='application/json'
        )
        
        # Check that Rule A is still in used_rule_ids
        # This is verified by checking the history
        history = self.client.session.get('assessment_history', [])
        
        # Q2 should still have rule_id = Rule A
        q2_entry = next((item for item in history if item['question_id'] == self.q2.id), None)
        self.assertIsNotNone(q2_entry)
        self.assertEqual(q2_entry['rule_id'], self.rule_a.id)
