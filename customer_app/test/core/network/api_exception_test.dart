import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:customer_app/core/network/api_exception.dart';

DioException _httpError(int status, Object? data) {
  final request = RequestOptions(path: 'test/');
  return DioException(
    requestOptions: request,
    response: Response<dynamic>(requestOptions: request, statusCode: status, data: data),
    type: DioExceptionType.badResponse,
  );
}

void main() {
  test('uses the detail message and code from the backend', () {
    final exception = ApiException.fromDio(_httpError(401, {
      'detail': 'Not signed in.',
      'code': 'not_authenticated',
    }));

    expect(exception.message, 'Not signed in.');
    expect(exception.code, 'not_authenticated');
    expect(exception.isUnauthorized, isTrue);
  });

  test('maps DRF field errors', () {
    final exception = ApiException.fromDio(_httpError(400, {
      'phone': ['Enter the phone number in international format.'],
    }));

    expect(exception.message, 'Enter the phone number in international format.');
    expect(exception.fieldErrors['phone'], 'Enter the phone number in international format.');
  });

  test('reports a connection failure when there is no response', () {
    final exception = ApiException.fromDio(DioException(
      requestOptions: RequestOptions(path: 'test/'),
      type: DioExceptionType.connectionError,
    ));

    expect(exception.isNetworkError, isTrue);
    expect(exception.statusCode, isNull);
  });
}
