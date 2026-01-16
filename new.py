// lib/screens/question_screen.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/api_endpoints.dart';
import 'test_results_screen.dart';

class QuestionScreen extends StatefulWidget {
  final int testId;
  final int questionNum;
  final String userId;
  final String testName;
  final int durationMinutes;
  
  const QuestionScreen({
    Key? key, 
    required this.testId,
    required this.questionNum,
    required this.userId,
    required this.testName,
    required this.durationMinutes,
  }) : super(key: key);

  @override
  _QuestionScreenState createState() => _QuestionScreenState();
}

class _QuestionScreenState extends State<QuestionScreen> {
  Map<String, dynamic>? questionData;
  bool isLoading = true;
  String? error;
  String? selectedAnswer;
  bool isMarked = false;
  int currentQNum = 1;
  int totalQuestions = 0;
  List<String> markedQuestions = [];
  int timeLeft = 0;
  bool showTimer = true;

  @override
  void initState() {
    super.initState();
    timeLeft = widget.durationMinutes * 60;
    _startTimer();
    loadQuestion();
  }

  void _startTimer() {
    Future.delayed(Duration(seconds: 1), () {
      if (mounted && timeLeft > 0) {
        setState(() => timeLeft--);
        _startTimer();
      } else if (timeLeft <= 0) {
        _showTimeUpDialog();
      }
    });
  }

  Future<void> loadQuestion() async {
    try {
      setState(() => isLoading = true);
      final response = await http.get(
        Uri.parse(ApiEndpoints.singleQuestion(widget.testId, widget.questionNum)),
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        questionData = json.decode(response.body);
        currentQNum = questionData?['q_num'] ?? widget.questionNum;
        totalQuestions = questionData?['total'] ?? 0;
        selectedAnswer = null;
        markedQuestions = [];
        isMarked = false;
        setState(() {});
      } else {
        setState(() => error = 'Failed to load question');
      }
    } catch (e) {
      setState(() => error = 'Network error: $e');
    } finally {
      setState(() => isLoading = false);
    }
  }

  Future<void> toggleMark() async {
    final response = await http.post(
      Uri.parse(ApiEndpoints.toggleMark(widget.testId, currentQNum)),
      headers: {'Content-Type': 'application/json'},
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      setState(() => isMarked = data['marked']);
    }
  }

  Future<void> submitAnswer(String nav) async {
    // ✅ Answer saving REMOVED - no ApiEndpoints.saveAnswer exists
    // TODO: Add your save answer API later when endpoint is ready

    if (nav == 'submit' || (currentQNum == totalQuestions && nav != 'previous')) {
      _showSubmitDialog();
      return;
    }

    int targetQNum = currentQNum;
    if (nav == 'next' || nav == 'skip') {
      targetQNum = currentQNum + 1;
    } else if (nav == 'previous' && currentQNum > 1) {
      targetQNum = currentQNum - 1;
    }

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => QuestionScreen(
          testId: widget.testId,
          questionNum: targetQNum,
          userId: widget.userId,
          testName: widget.testName,
          durationMinutes: widget.durationMinutes,
        ),
      ),
    );
  }

  void _showSubmitDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text('Submit Test'),
        content: Text('Are you sure you want to submit the test?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Continue'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            onPressed: () {
              Navigator.pop(context);
              _submitTest();
            },
            child: Text('Submit Test'),
          ),
        ],
      ),
    );
  }

  Future<void> _submitTest() async {
    final response = await http.post(
      Uri.parse(ApiEndpoints.submitTest(widget.testId)),
      headers: {'Content-Type': 'application/json'},
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => TestResultsScreen(
            testId: widget.testId.toString(),
            scores: data['scores'],
            userId: widget.userId,
          ),
        ),
      );
    }
  }

  void _showTimeUpDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text('Time Up!'),
        content: Text('Time is up! Submitting test automatically.'),
        actions: [
          ElevatedButton(
            onPressed: () => _submitTest(),
            child: Text('Submit'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    
    if (error != null) {
      return Scaffold(
        body: Center(child: Text(error!, style: TextStyle(color: Colors.red))),
      );
    }

    final question = questionData!['question'];
    
    return Scaffold(
      backgroundColor: Color(0xFFF0F0F5),
      body: Column(
        children: [
          // Question Header
          Container(
            width: double.infinity,
            color: Color(0xFF003087),
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${widget.testName} – Question $currentQNum of $totalQuestions',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 15,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                        GestureDetector(
                          onTap: toggleMark,
                          child: Container(
                            padding: EdgeInsets.all(6),
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: isMarked ? Colors.yellow[700] : Colors.transparent,
                            ),
                            child: Text(
                              isMarked ? '★' : '☆',
                              style: TextStyle(
                                fontSize: 26,
                                color: isMarked ? Colors.black : Colors.white70,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(width: 12),
                  ElevatedButton(
                    onPressed: () {
                      // Navigate to review
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      shadowColor: Colors.transparent,
                      side: BorderSide(color: Colors.white.withOpacity(0.5)),
                    ),
                    child: Text('Review', style: TextStyle(color: Colors.white)),
                  ),
                ],
              ),
            ),
          ),
          
          // Question Content
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.all(16),
              child: Container(
                margin: EdgeInsets.all(20),
                padding: EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 10, offset: Offset(0, 2)),
                  ],
                  border: Border(left: BorderSide(color: Color(0xFF003087), width: 5)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Question Image (if exists)
                    if (question['images'] != null)
                      Container(
                        margin: EdgeInsets.only(bottom: 24),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.memory(
                            base64Decode(question['images']),
                            height: 380,
                            fit: BoxFit.contain,
                          ),
                        ),
                      ),
                    
                    // Question Text
                    Container(
                      margin: EdgeInsets.only(bottom: 24),
                      child: Text(
                        question['question'] ?? '',
                        style: TextStyle(
                          fontSize: 18,
                          height: 1.6,
                          color: Color(0xFF222222),
                        ),
                      ),
                    ),
                    
                    // Options (FIXED)
                    ...['A', 'B', 'C', 'D'].map((opt) {
                      final optionText = question['option_${opt.toLowerCase()}']?.toString() ?? '';
                      if (optionText.isEmpty) return SizedBox.shrink();
                      
                      final isSelected = selectedAnswer == opt;
                      
                      return Container(
                        margin: EdgeInsets.only(bottom: 12),
                        child: GestureDetector(
                          onTap: () {
                            setState(() {
                              selectedAnswer = opt;
                            });
                          },
                          child: Container(
                            padding: EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                            decoration: BoxDecoration(
                              color: isSelected 
                                  ? Color(0xFFE9F1FF)
                                  : Color(0xFFF8F9FA),
                              borderRadius: BorderRadius.circular(8),
                              border: Border(
                                left: BorderSide(
                                  color: isSelected ? Color(0xFF003087) : Color(0xFF6C757D),
                                  width: 4,
                                ),
                              ),
                            ),
                            child: Row(
                              children: [
                                Radio<String>(
                                  value: opt,
                                  groupValue: selectedAnswer,
                                  onChanged: (value) {
                                    setState(() {
                                      selectedAnswer = value;
                                    });
                                  },
                                  activeColor: Color(0xFF003087),
                                ),
                                SizedBox(width: 12),
                                Expanded(child: Text(optionText)),
                              ],
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ],
                ),
              ),
            ),
          ),
          
          // Fixed Bottom Navigation (FIXED)
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.12),
                  blurRadius: 14,
                  offset: Offset(0, -3),
                ),
              ],
              border: Border(top: BorderSide(color: Color(0xFFD0D0D8))),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  // Previous Button
                  if (currentQNum > 1)
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () => submitAnswer('previous'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Color(0xFF6C757D),
                          foregroundColor: Colors.white,
                          padding: EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        child: Text('← Previous'),
                      ),
                    )
                  else
                    SizedBox(width: 130),
                  
                  SizedBox(width: 12),
                  
                  // Main Action Button (Skip/Next/Submit) - FIXED
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: selectedAnswer != null 
                          ? () => submitAnswer(
                              currentQNum == totalQuestions ? 'submit' : 'next'
                            )
                          : () => submitAnswer('skip'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: selectedAnswer != null 
                            ? (currentQNum == totalQuestions ? Colors.green : Color(0xFF003087))
                            : Color(0xFF9E9E9E),
                        foregroundColor: Colors.white,
                        padding: EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      child: Text(
                        currentQNum == totalQuestions 
                            ? 'Submit Test'
                            : (selectedAnswer != null ? 'Next →' : 'Skip'),
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      
      // Floating Timer
      floatingActionButtonLocation: FloatingActionButtonLocation.endTop,
      floatingActionButton: showTimer
          ? Container(
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.7),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                'Time: ${_formatTime(timeLeft)}',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            )
          : null,
    );
  }

  String _formatTime(int seconds) {
    final minutes = (seconds ~/ 60).toString().padLeft(2, '0');
    final secs = (seconds % 60).toString().padLeft(2, '0');
    return '$minutes:$secs';
  }
}
