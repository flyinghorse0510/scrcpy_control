#include <cstdio>



class SupportLine
{
public:
    long long _primaryBufferPoint;
    long long _primaryBufferCount;
    long long _auxiliaryBufferPoint;
    long long _auxiliaryBufferCount;
    long long _supportPoint;
    long long _minConfirmCount;
    long long _increMinConfirmCount;
    SupportLine(long long minConfirmCount = 5)
    {
        _primaryBufferPoint = 0;
        _primaryBufferCount = 0;
        _auxiliaryBufferPoint = 0;
        _auxiliaryBufferCount = 0;
        _supportPoint = 0;
        _minConfirmCount = minConfirmCount;
        _increMinConfirmCount = (minConfirmCount + 1) / 2;
    }

    void reset_support_line(void)
    {
        _primaryBufferPoint = 0;
        _primaryBufferCount = 0;
        _auxiliaryBufferPoint = 0;
        _auxiliaryBufferCount = 0;
        _supportPoint = 0;
    }

    long long update_support_line(long long measurePoint)
    {
        if (measurePoint < 0)
        {
            return _supportPoint;
        }

        std::fprintf(stderr, "Support point: %lld, Primary buffer point: %lld, Primary buffer count: %lld, Auxiliary buffer Point: %lld, Auxiliary buffer count: %lld, Measure point: %lld\n", _supportPoint, _primaryBufferPoint, _primaryBufferCount, _auxiliaryBufferPoint, _auxiliaryBufferCount, measurePoint);
        std::fflush(stderr);

        if (measurePoint == _supportPoint) {
            _primaryBufferPoint = 0;
            _primaryBufferCount = 0;
            _auxiliaryBufferPoint = 0;
            _auxiliaryBufferCount = 0;
            return _supportPoint;
        }

        if (measurePoint < _supportPoint)
        {
            // std::fprintf(stderr, "[SUPPORT LINE WARNING]: Support point: %lld, Buffer point: %lld, Buffer count: %lld, Measure point: %lld\n", _supportPoint, _bufferPoint, _bufferCount, measurePoint);
            // std::fflush(stderr);
            // return _supportPoint;
        }

        if (_primaryBufferCount == 0) {
            _primaryBufferPoint = measurePoint;
            _primaryBufferCount++;
            return _supportPoint;
        }

        if (measurePoint < _primaryBufferPoint) {
            _primaryBufferPoint = measurePoint;
            _primaryBufferCount = 1;
            _auxiliaryBufferPoint = 0;
            _auxiliaryBufferCount = 0;
            return _supportPoint;
        }

        if (measurePoint == _primaryBufferPoint) {
            _primaryBufferCount++;
            if (_primaryBufferCount >= _minConfirmCount) {
                _supportPoint = _primaryBufferPoint;
                _primaryBufferPoint = _auxiliaryBufferPoint;
                _primaryBufferCount = _auxiliaryBufferCount;
                _auxiliaryBufferPoint = 0;
                _auxiliaryBufferCount = 0;
                return _supportPoint;
            }
            if (_primaryBufferCount >= _increMinConfirmCount) {
                if (_auxiliaryBufferCount >= _increMinConfirmCount) {
                    _supportPoint = _primaryBufferPoint;
                    _primaryBufferPoint = _auxiliaryBufferPoint;
                    _primaryBufferCount = _auxiliaryBufferCount;
                    _auxiliaryBufferPoint = 0;
                    _auxiliaryBufferCount = 0;
                    return _supportPoint;
                }
            }
            return _supportPoint;
        }

        if (_auxiliaryBufferCount > 0 && measurePoint < _auxiliaryBufferPoint) {
            if (_primaryBufferCount >= _auxiliaryBufferCount) {
                _auxiliaryBufferPoint = measurePoint;
                _auxiliaryBufferCount = 1;
            } else {
                _primaryBufferPoint = measurePoint;
                _primaryBufferCount = 1;
            }
            return _supportPoint;
        }

        if (_auxiliaryBufferCount > 0 && measurePoint > _auxiliaryBufferPoint) {
            if (_primaryBufferCount >= _auxiliaryBufferCount) {
                _auxiliaryBufferPoint = measurePoint;
                _auxiliaryBufferCount = 1;
            } else {
                _primaryBufferPoint = _auxiliaryBufferPoint;
                _primaryBufferCount = _auxiliaryBufferCount;
                _auxiliaryBufferPoint = measurePoint;
                _auxiliaryBufferCount = 1;
            }
            return _supportPoint;
        }

        if (_auxiliaryBufferCount > 0 && measurePoint == _auxiliaryBufferPoint) {
            _auxiliaryBufferCount++;
            if (_auxiliaryBufferCount >= _minConfirmCount) {
                _supportPoint = _auxiliaryBufferPoint;
                _primaryBufferPoint = 0;
                _primaryBufferCount = 0;
                _auxiliaryBufferPoint = 0;
                _auxiliaryBufferCount = 0;
                return _supportPoint;
            }
            if (_auxiliaryBufferCount >= _increMinConfirmCount) {
                if (_primaryBufferCount >= _increMinConfirmCount) {
                    _supportPoint = _primaryBufferPoint;
                    _primaryBufferPoint = _auxiliaryBufferPoint;
                    _primaryBufferCount = _auxiliaryBufferCount + 1;
                    _auxiliaryBufferPoint = 0;
                    _auxiliaryBufferCount = 0;
                    return _supportPoint;
                }
            }
            return _supportPoint;
        }

        if (_auxiliaryBufferCount == 0 && measurePoint > _primaryBufferPoint) {
            _auxiliaryBufferPoint = measurePoint;
            _auxiliaryBufferCount = 1;
            return _supportPoint;
        }

        std::fprintf(stdout, "[SUPPORT LINE FATAL ERROR]: Unbounded situation!\nSupport point: %lld, Primary buffer point: %lld, Primary buffer count: %lld, Auxiliary buffer Point: %lld, Auxiliary buffer count: %lld, Measure point: %lld\n", _supportPoint, _primaryBufferPoint, _primaryBufferCount, _auxiliaryBufferPoint, _auxiliaryBufferCount, measurePoint);
        std::fflush(stdout);
        return _supportPoint;
    }

    long long get_support_point(void) {
        return _supportPoint;
    }
};