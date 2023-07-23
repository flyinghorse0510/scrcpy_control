#include <cstdio>



class SupportLine
{
public:
    long long _bufferPoint;
    long long _bufferCount;
    long long _supportPoint;
    long long _minConfirmCount;
    SupportLine(long long minConfirmCount = 3)
    {
        _bufferPoint = -1;
        _bufferCount = 0;
        _supportPoint = -1;
        _minConfirmCount = minConfirmCount;
    }

    void reset_support_line(void)
    {
        _bufferPoint = -1;
        _bufferCount = 0;
        _supportPoint = -1;
    }

    long long update_support_line(long long measurePoint)
    {
        if (measurePoint < 0)
        {
            return _supportPoint;
        }

        if (measurePoint < _supportPoint)
        {
            std::fprintf(stderr, "[SUPPORT LINE WARNING]: Support point: %lld, Buffer point: %lld, Buffer count: %lld, Measure point: %lld\n", _supportPoint, _bufferPoint, _bufferCount, measurePoint);
            std::fflush(stderr);
            return _supportPoint;
        }

        if (measurePoint == _supportPoint)
        {
            return _supportPoint;
        }

        if (_bufferCount == 0)
        {
            _bufferPoint = measurePoint;
            _bufferCount++;
            return _supportPoint;
        }

        if (measurePoint < _bufferPoint)
        {
            _bufferCount = 1;
            _bufferPoint = measurePoint;
            return _supportPoint;
        }

        if (measurePoint > _bufferPoint)
        {
            _supportPoint = _bufferPoint;
            _bufferPoint = measurePoint;
            _bufferCount = 1;
            return _supportPoint;
        }

        if (measurePoint == _bufferPoint)
        {
            if (_bufferCount == _minConfirmCount - 1)
            {
                _supportPoint = _bufferPoint;
                _bufferCount = 0;
            }
            else
            {
                _bufferCount++;
            }
            return _supportPoint;
        }

        std::fprintf(stdout, "[SUPPORT LINE FATAL ERROR]: Unbounded situation!\nSupport point: %lld, Buffer point: %lld, Buffer count: %lld, Measure point: %lld\n", _supportPoint, _bufferPoint, _bufferCount, measurePoint);
        std::fflush(stdout);
        return _supportPoint;
    }

    long long get_support_point(void) {
        return _supportPoint;
    }
};